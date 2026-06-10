import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_MODEL = "deepseek/deepseek-v4-flash"
VISION_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"


async def analyze_mood_text(text: str, events: str = "") -> dict:
    prompt = f"""
    Analyze the emotional state of the user based on:
    Message: {text}
    Recent events: {events}

    Return ONLY valid JSON in this exact format:
    {{
      "emotion": "happy|sad|anxious|excited|angry|romantic|nostalgic|bored|stressed|hopeful",
      "intensity": 0.8,
      "genres": ["Comedy", "Romance"],
      "summary": "You seem upbeat and energetic today.",
      "movie_prompt": "light-hearted comedies with happy endings"
    }}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",
            },
            json={
                "model": TEXT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
    data = resp.json()
    if "choices" not in data:
        err = data.get("error", {})
        raise Exception(err.get("message", "OpenRouter API error"))
    raw = data["choices"][0]["message"]["content"]
    clean = raw.strip().replace("```json", "").replace("```", "")
    return json.loads(clean)


async def analyze_mood_image(image_base64: str) -> dict:
    prompt = """
    Look at this person's facial expression carefully.
    Determine their emotional state.
    Return ONLY valid JSON:
    {
      "emotion": "happy|sad|anxious|excited|angry|neutral|tired",
      "intensity": 0.7,
      "genres": ["Comedy", "Adventure"],
      "summary": "You look cheerful and energetic!",
      "movie_prompt": "fun adventure films"
    }
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",
            },
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
            timeout=30,
        )
    data = resp.json()
    if "choices" not in data:
        err = data.get("error", {})
        raise Exception(err.get("message", "OpenRouter API error"))
    raw = data["choices"][0]["message"]["content"]
    return json.loads(raw.strip().replace("```json", "").replace("```", ""))


_movie_emotion_cache = {}


async def analyze_movie_emotions(title: str, overview: str, genre_names: list) -> dict:
    cache_key = f"{title}|{overview[:100]}"
    if cache_key in _movie_emotion_cache:
        return _movie_emotion_cache[cache_key]

    genres_str = ", ".join(genre_names) if genre_names else "General"
    prompt = f"""Analyze the emotional profile of this movie:
Title: {title}
Genres: {genres_str}
Plot: {overview[:500]}

Return ONLY valid JSON with emotion scores (0-100) for these dimensions:
{{
  "excitement": 85,
  "humor": 20,
  "romance": 10,
  "tension": 70,
  "sadness": 40,
  "fear": 15,
  "inspiration": 60,
  "intrigue": 90,
  "warmth": 30,
  "nostalgia": 25,
  "best_mood": "adventurous",
  "best_time": "evening",
  "vibe_tags": ["thrilling", "mind-bending", "intense"]
}}
best_mood should be one of: happy, sad, excited, relaxed, romantic, scared, thoughtful, adventurous, nostalgic, funny
best_time should be one of: morning, afternoon, evening, late_night, anytime
vibe_tags should be 2-3 short descriptive words
"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",
            },
            json={
                "model": TEXT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
    data = resp.json()
    if "choices" not in data:
        return _default_emotions()
    raw = data["choices"][0]["message"]["content"]
    try:
        result = json.loads(raw.strip().replace("```json", "").replace("```", ""))
        _movie_emotion_cache[cache_key] = result
        return result
    except Exception:
        return _default_emotions()


def _default_emotions():
    return {
        "excitement": 50, "humor": 50, "romance": 50, "tension": 50,
        "sadness": 50, "fear": 50, "inspiration": 50, "intrigue": 50,
        "warmth": 50, "nostalgia": 50,
        "best_mood": "happy", "best_time": "anytime", "vibe_tags": ["entertaining"],
    }


async def chat_with_gemini(messages: list, mood: dict = None, prescription_movies: list = None, search_query: str = None) -> str:
    context = ""
    if mood:
        context = f"The user is feeling {mood.get('emotion', 'unknown')}. "
        context += f"Mood summary: {mood.get('summary', '')}"

    if search_query:
        system_prompt = f"""
        You are CineMood AI, a personal movie & series assistant and encyclopedia.
        The user searched for: "{search_query}".
        Provide detailed info about the movie, series, actor, or topic they're asking about.
        Include release year, cast, plot summary, and why it's worth watching.
        Be enthusiastic and knowledgeable. Keep it 4-6 sentences.
        """
    else:
        movie_context = ""
        if prescription_movies:
            titles = [m.get("title", m.get("name", "")) for m in prescription_movies[:15]]
            movie_context = "\n\nPrescribed films for therapy:\n"
            for t in titles:
                movie_context += f"- {t}\n"
            movie_context += "\nIn your response, EXPLICITLY reference 2-3 of these titles and explain why they match the user's emotional state."

        system_prompt = f"""
        You are CineMood AI, a personal movie therapist and film connoisseur. {context}
        You have deep knowledge of cinema and can discuss any movie, actor, director, or genre.
        Keep responses warm, insightful, and concise (3-5 sentences).
        {movie_context}
        """
    formatted = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",
            },
            json={
                "model": TEXT_MODEL,
                "messages": [{"role": "system", "content": system_prompt}, *formatted],
            },
            timeout=30,
        )
    data = resp.json()
    if "choices" not in data:
        err = data.get("error", {})
        raise Exception(err.get("message", "OpenRouter API error"))
    raw = data["choices"][0]["message"]["content"]
    return raw
