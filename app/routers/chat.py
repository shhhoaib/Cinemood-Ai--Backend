from fastapi import APIRouter, HTTPException, Body
from app.models.schemas import ChatRequest
from app.services.gemini import chat_with_gemini, analyze_mood_text
from app.services.tmdb import get_movies_for_mood, search_movies, search_multi, format_movie
from app.services.prescriptions import PRESCRIPTIONS
import random, re, asyncio, httpx

router = APIRouter()

MOOD_KEYWORDS = {
    "sad": "sadness", "sadness": "sadness", "depressed": "sadness", "unhappy": "sadness", "crying": "sadness", "grief": "sadness", "mourning": "sadness",
    "anxious": "anxiety", "anxiety": "anxiety", "worried": "anxiety", "nervous": "anxiety", "panic": "anxiety", "overthinking": "anxiety",
    "stress": "stress", "stressed": "stress", "overwhelmed": "stress", "pressure": "stress", "burned out": "burnout", "burnout": "burnout",
    "tired": "burnout", "exhausted": "burnout", "drained": "burnout",
    "heartbroken": "heartbreak", "heartbreak": "heartbreak", "breakup": "heartbreak", "love": "heartbreak", "lonely": "heartbreak",
    "alone": "loneliness", "loneliness": "loneliness", "isolated": "loneliness",
    "angry": "anger", "anger": "anger", "frustrated": "anger", "rage": "anger", "furious": "anger",
    "scared": "scared", "afraid": "scared", "fear": "scared", "terrified": "scared",
    "hopeful": "hope", "hope": "hope", "inspired": "hope",
    "nostalgic": "nostalgia", "nostalgia": "nostalgia",
    "existential": "existential", "confused": "existential", "lost": "existential",
    "creative": "creativity", "block": "creativity", "art": "creativity", "write": "creativity",
}

RELATED_CATEGORIES = {
    "sadness": ["sadness", "heartbreak", "loneliness", "hope"],
    "anxiety": ["anxiety", "stress", "scared", "hope"],
    "stress": ["stress", "anxiety", "burnout", "nostalgia"],
    "heartbreak": ["heartbreak", "sadness", "loneliness", "creativity"],
    "loneliness": ["loneliness", "sadness", "heartbreak", "hope"],
    "anger": ["anger", "stress", "existential", "creativity"],
    "burnout": ["burnout", "stress", "creativity", "nostalgia"],
    "hope": ["hope", "creativity", "nostalgia", "sadness"],
    "existential": ["existential", "creativity", "hope", "scared"],
    "creativity": ["creativity", "hope", "existential", "nostalgia"],
    "scared": ["scared", "stress", "existential", "hope"],
    "nostalgia": ["nostalgia", "hope", "sadness", "creativity"],
}


def detect_prescription_key(text: str) -> str:
    text_lower = text.lower()
    for word, mood_key in MOOD_KEYWORDS.items():
        if word in text_lower:
            return mood_key
    return "sadness"


SEARCH_TRIGGERS = [
    r"search\s+(?:for\s+)?(.+)", r"find\s+(?:me\s+)?(.+)", r"show\s+(?:me\s+)?(.+)",
    r"recommend\s+(?:me\s+)?(.+)", r"looking\s+(?:for\s+)?(.+)", r"movies?\s+(?:like\s+|about\s+|with\s+)(.+)",
    r"tell\s+me\s+about\s+(.+)", r"what\s+(?:is|are)\s+(.+)", r"who\s+(?:is|are|played|directed)\s+(.+)",
    r"(\w+)\s+(?:movie|film|series|show|actor|director)",
]


def detect_search_query(text: str) -> str:
    text_lower = text.lower().strip()
    for pattern in SEARCH_TRIGGERS:
        m = re.search(pattern, text_lower)
        if m:
            q = m.group(1).strip()
            if len(q) > 2:
                return q
    if len(text_lower) > 3 and not any(w in text_lower for w in ["feel", "sad", "happy", "stress", "anxi", "angry", "lonely", "scared", "tired", "love", "hate"]):
        return text_lower
    return ""


@router.post("/message")
async def chat_message(req: ChatRequest):
    try:
        movies = []
        mood_result = None
        genre_names = None
        search_source = None

        all_text = " ".join(m.get("content", "") for m in req.messages if m.get("role") == "user")
        detected_mood_key = detect_prescription_key(all_text)

        # Check for search intent
        last_msg = req.messages[-1].get("content", "") if req.messages else ""
        search_query = detect_search_query(last_msg)

        if search_query:
            try:
                search_results = await search_multi(search_query, page=1)
                movies = search_results[:30]
                search_source = search_query
            except Exception:
                pass

        if not movies:
            # Merge 3 related prescription categories for 200+ total
            related = RELATED_CATEGORIES.get(detected_mood_key, [detected_mood_key])
            picks = []
            seen_titles = set()
            for cat in related:
                if cat in PRESCRIPTIONS:
                    cat_movies = PRESCRIPTIONS[cat].get("movies", [])
                    cat_series = PRESCRIPTIONS[cat].get("series", [])
                    for item in cat_movies + cat_series:
                        t = item.get("title", item.get("name", "")).lower()
                        if t not in seen_titles:
                            seen_titles.add(t)
                            picks.append(item)

            random.shuffle(picks)
            picks = picks[:210]

            # Enrich prescription picks with TMDB posters
            sem = asyncio.Semaphore(5)

            async def enrich_prescription(pick):
                title = pick.get("title", pick.get("name", ""))
                year = pick.get("year", "")
                async with sem:
                    try:
                        results = await search_movies(f"{title} {year}".strip(), page=1)
                        if results:
                            r = results[0]
                            r["reason"] = pick.get("reason", "")
                            r["prescription_title"] = title
                            return r
                    except Exception:
                        pass
                return {
                    "id": abs(hash(title)) % 10**9,
                    "title": title,
                    "year": year,
                    "reason": pick.get("reason", ""),
                    "prescription_title": title,
                    "media_type": "series" if pick.get("name") else "movie",
                    "rating": 0,
                    "poster": None,
                }

            enriched = await asyncio.gather(*[enrich_prescription(p) for p in picks])
            movies = [e for e in enriched if e]

        if req.mood and req.mood.get("genres"):
            genre_names = req.mood["genres"]
        elif req.messages and len(req.messages) > 0:
            if len(last_msg) > 5:
                try:
                    mood_result = await analyze_mood_text(last_msg)
                    genre_names = mood_result.get("genres", [])
                except Exception:
                    pass
        if not genre_names:
            genre_names = ["Action", "Comedy", "Drama"]

        try:
            tmdb_movies = await get_movies_for_mood(genre_names, top_n=100)
            existing_ids = {m.get("id") for m in movies}
            for m in tmdb_movies:
                if m.get("id") not in existing_ids:
                    movies.append(m)
        except Exception:
            pass

        reply = await chat_with_gemini(req.messages, req.mood, prescription_movies=movies[:15], search_query=search_query)

        prescription_data = None
        if not search_query:
            prescription = PRESCRIPTIONS.get(detected_mood_key, PRESCRIPTIONS["sadness"])
            prescription_data = {
                "category": detected_mood_key,
                "name": prescription["name"],
                "emoji": prescription["emoji"],
                "description": prescription["description"],
            }

        return {
            "reply": reply,
            "movies": movies,
            "mood": mood_result or req.mood,
            "prescription": prescription_data,
            "search_query": search_query or None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
