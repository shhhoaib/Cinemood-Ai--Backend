import httpx
import json
import os
import random
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TMDB_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"
def _today():
    return datetime.now().strftime("%Y-%m-%d")

GENRE_MAP = {
    "Action": 28, "Comedy": 35, "Drama": 18, "Horror": 27,
    "Romance": 10749, "Thriller": 53, "Animation": 16,
    "Documentary": 99, "Fantasy": 14, "Science Fiction": 878,
    "Adventure": 12, "Mystery": 9648, "Family": 10751,
    "War": 10752, "History": 36, "Music": 10402, "Western": 37,
    "Crime": 80, "TV Movie": 10770,
    "Sport": 10770, "Superhero": 28, "Psychological": 53,
    "Suspense": 53, "Spy": 9648, "Biography": 36,
    "Sports": 10770, "Musical": 10402, "Noir": 80,
    "Comfort Film": 18, "Feel Good": 35, "Heartwarming": 10751,
    "Inspirational": 18, "Uplifting": 18, "Relaxing": 35,
}
ID_TO_GENRE = {v: k for k, v in GENRE_MAP.items()}


def normalize_genres(genres: list) -> list:
    result = []
    for g in genres:
        if g in GENRE_MAP:
            result.append(g)
        else:
            gl = g.lower()
            found = False
            for key in GENRE_MAP:
                if gl in key.lower() or key.lower() in gl:
                    result.append(key)
                    found = True
                    break
            if not found:
                for key, val in GENRE_MAP.items():
                    if val == 18 or val == 35 or val == 28:
                        result.append(key)
                        break
    return list(dict.fromkeys(result))


def format_movie(m: dict) -> dict:
    genre_ids = m.get("genre_ids", [])
    if not genre_ids and m.get("genres"):
        genre_ids = [g["id"] for g in m["genres"]]
    return {
        "id": m["id"],
        "title": m["title"],
        "media_type": "movie",
        "poster": f"{IMG_BASE}/w500{m['poster_path']}" if m.get("poster_path") else None,
        "poster_small": f"{IMG_BASE}/w342{m['poster_path']}" if m.get("poster_path") else None,
        "backdrop": f"{IMG_BASE}/w1280{m['backdrop_path']}" if m.get("backdrop_path") else None,
        "rating": m["vote_average"],
        "year": m["release_date"][:4] if m.get("release_date") else "?",
        "release_date": m.get("release_date", ""),
        "overview": m.get("overview", ""),
        "genre_ids": genre_ids,
        "genre_names": [ID_TO_GENRE.get(gid) for gid in genre_ids if ID_TO_GENRE.get(gid)],
    }


def format_tv(t: dict) -> dict:
    genre_ids = t.get("genre_ids", [])
    if not genre_ids and t.get("genres"):
        genre_ids = [g["id"] for g in t["genres"]]
    return {
        "id": t["id"],
        "title": t.get("name", ""),
        "media_type": "tv",
        "poster": f"{IMG_BASE}/w500{t['poster_path']}" if t.get("poster_path") else None,
        "poster_small": f"{IMG_BASE}/w342{t['poster_path']}" if t.get("poster_path") else None,
        "backdrop": f"{IMG_BASE}/w1280{t['backdrop_path']}" if t.get("backdrop_path") else None,
        "rating": t["vote_average"],
        "year": t.get("first_air_date", "")[:4] if t.get("first_air_date") else "?",
        "overview": t.get("overview", ""),
        "genre_ids": genre_ids,
        "genre_names": [ID_TO_GENRE.get(gid) for gid in genre_ids if ID_TO_GENRE.get(gid)],
    }


# --- MOVIES ---

async def get_movies_for_mood(genres: list, top_n: int = 60) -> list:
    genres = normalize_genres(genres)
    genre_ids = ",".join(str(GENRE_MAP[g]) for g in genres if g in GENRE_MAP)
    if not genre_ids:
        return []
    seen = set()
    all_movies = []
    for page in [1, 2, 3]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/discover/movie",
                params={
                    "api_key": TMDB_KEY,
                    "with_genres": genre_ids,
                    "sort_by": "popularity.desc",
                    "vote_count.gte": 50,
                    "page": page,
                },
            )
        for m in resp.json().get("results", []):
            mid = m.get("id")
            if mid not in seen:
                seen.add(mid)
                all_movies.append(m)
    return [format_movie(m) for m in all_movies[:top_n]]


async def get_trending_movies() -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/trending/movie/week",
            params={"api_key": TMDB_KEY, "page": random.randint(1, 3)},
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:15]]


async def get_trending_tv() -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/trending/tv/week",
            params={"api_key": TMDB_KEY, "page": random.randint(1, 3)},
        )
    return [format_tv(t) for t in resp.json().get("results", [])[:10]]


async def get_popular_movies(page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": TMDB_KEY, "page": page},
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


async def get_popular_tv(page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/tv/popular",
            params={"api_key": TMDB_KEY, "page": page},
        )
    return [format_tv(t) for t in resp.json().get("results", [])[:20]]


async def get_top_rated_movies(page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/movie/top_rated",
            params={"api_key": TMDB_KEY, "page": page},
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


async def get_by_genre(genre_id: int, page: int = None) -> list:
    if page is None:
        page = random.randint(1, 5)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/discover/movie",
            params={
                "api_key": TMDB_KEY,
                "with_genres": genre_id,
                "sort_by": random.choice(["popularity.desc", "vote_average.desc"]),
                "vote_count.gte": 50,
                "page": page,
                "primary_release_date.lte": _today(),
            },
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


INDUSTRIES = {
    "bollywood": {"name": "Bollywood", "code": "hi", "flag": "\U0001f1ee\U0001f1f3", "description": "Hindi Cinema (Bollywood)", "region": "IN"},
    "hollywood": {"name": "Hollywood", "code": "en", "flag": "\U0001f1fa\U0001f1f8", "description": "English Cinema (Hollywood)", "region": "US"},
    "korean": {"name": "Korean", "code": "ko", "flag": "\U0001f1f0\U0001f1f7", "description": "Korean Cinema & K-Drama", "region": "KR"},
    "anime": {"name": "Anime", "code": "ja", "flag": "\U0001f1ef\U0001f1f5", "description": "Japanese Animation", "genre": 16, "region": "JP"},
    "tamil": {"name": "Tamil", "code": "ta", "flag": "\U0001f1ee\U0001f1f3", "description": "Tamil Cinema (Kollywood)", "region": "IN"},
    "telugu": {"name": "Telugu", "code": "te", "flag": "\U0001f1ee\U0001f1f3", "description": "Telugu Cinema (Tollywood)", "region": "IN"},
    "punjabi": {"name": "Punjabi", "code": "pa", "flag": "\U0001f1ee\U0001f1f3", "description": "Punjabi Cinema", "region": "IN"},
    "pakistani": {"name": "Pakistani", "code": "ur", "flag": "\U0001f1f5\U0001f1f0", "description": "Urdu Cinema (Pakistan)", "region": "PK"},
    "bengali": {"name": "Bengali", "code": "bn", "flag": "\U0001f1e7\U0001f1e9", "description": "Bengali Cinema", "region": "IN"},
    "turkish": {"name": "Turkish", "code": "tr", "flag": "\U0001f1f9\U0001f1f7", "description": "Turkish Cinema & Series", "region": "TR"},
}


SUBCATEGORIES = {
    "trending": {"sort_by": "popularity.desc", "label": "Trending"},
    "top-rated": {"sort_by": "vote_average.desc", "label": "Top Rated", "vote_count": 200},
    "latest": {"sort_by": "primary_release_date.desc", "label": "Latest", "from_year": 2024},
    "action": {"sort_by": "popularity.desc", "label": "Action", "genre": 28},
    "romance": {"sort_by": "popularity.desc", "label": "Romance", "genre": 10749},
    "comedy": {"sort_by": "popularity.desc", "label": "Comedy", "genre": 35},
    "drama": {"sort_by": "popularity.desc", "label": "Drama", "genre": 18},
    "thriller": {"sort_by": "popularity.desc", "label": "Thriller", "genre": 53},
    "horror": {"sort_by": "popularity.desc", "label": "Horror", "genre": 27},
    "animation": {"sort_by": "popularity.desc", "label": "Animation", "genre": 16},
    "scifi": {"sort_by": "popularity.desc", "label": "Sci-Fi", "genre": 878},
}


TV_SUBCATEGORIES = {
    "trending": {"sort_by": "popularity.desc", "label": "Trending"},
    "top-rated": {"sort_by": "vote_average.desc", "label": "Top Rated", "vote_count": 200},
    "latest": {"sort_by": "first_air_date.desc", "label": "Latest", "from_year": 2024},
    "action": {"sort_by": "popularity.desc", "label": "Action", "genre": 10759},
    "romance": {"sort_by": "popularity.desc", "label": "Romance", "genre": 10749},
    "comedy": {"sort_by": "popularity.desc", "label": "Comedy", "genre": 35},
    "drama": {"sort_by": "popularity.desc", "label": "Drama", "genre": 18},
    "thriller": {"sort_by": "popularity.desc", "label": "Thriller", "genre": 53},
    "horror": {"sort_by": "popularity.desc", "label": "Horror", "genre": 9648},
    "animation": {"sort_by": "popularity.desc", "label": "Animation", "genre": 16},
    "scifi": {"sort_by": "popularity.desc", "label": "Sci-Fi", "genre": 10765},
}


async def get_by_industry(industry_id: str, page: int = 1, subcategory: str = None, media_type: str = "movie", watch_provider: str = None) -> list[dict]:
    industry = INDUSTRIES.get(industry_id)
    if not industry:
        return []

    is_tv = media_type == "tv"
    discover_url = f"{BASE_URL}/discover/tv" if is_tv else f"{BASE_URL}/discover/movie"
    subs = TV_SUBCATEGORIES if is_tv else SUBCATEGORIES
    date_field = "first_air_date" if is_tv else "primary_release_date"

    params = {
        "api_key": TMDB_KEY,
        "with_original_language": industry["code"],
        "page": page,
        "sort_by": "popularity.desc",
        f"{date_field}.lte": _today(),
    }

    if is_tv:
        params["without_genres"] = "10763,10764,10767"

    industry_genre = industry.get("genre")
    if subcategory and subcategory in subs:
        sub = subs[subcategory]
        params["sort_by"] = sub.get("sort_by", params["sort_by"])
        if sub.get("genre"):
            if industry_genre:
                params["with_genres"] = f"{industry_genre},{sub['genre']}"
            else:
                params["with_genres"] = str(sub["genre"])
        elif industry_genre:
            params["with_genres"] = str(industry_genre)
    elif industry_genre:
        params["with_genres"] = str(industry_genre)
        if sub.get("vote_count"):
            params["vote_count.gte"] = sub["vote_count"]
        if sub.get("from_year"):
            params[f"{date_field}.gte"] = f"{sub['from_year']}-01-01"

    if watch_provider:
        params["with_watch_providers"] = watch_provider
        params["watch_region"] = industry.get("region", "PK")

    async with httpx.AsyncClient() as client:
        resp = await client.get(discover_url, params=params)
    if resp.status_code != 200:
        return []
    results = resp.json().get("results", [])
    if is_tv:
        return [format_tv(t) for t in results]
    return [format_movie(m) for m in results]


def _pick_best_trailer(videos: list) -> str | None:
    if not videos:
        return None
    type_order = {"Trailer": 0, "Teaser": 1, "Featurette": 2, "Clip": 3}
    candidates = []
    for v in videos:
        if v.get("site") != "YouTube":
            continue
        vtype = v.get("type", "")
        if vtype not in type_order:
            continue
        lang = v.get("iso_639_1", "")
        type_rank = type_order[vtype]
        official = 0 if v.get("official") else 1
        lang_rank = 0 if lang == "en" else (1 if lang == "hi" else 2)
        candidates.append((type_rank, official, lang_rank, v.get("key", "")))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]


_yt_search_cache = {}


def _search_yt_trailer(title: str, year: int | str = "") -> str | None:
    import yt_dlp
    query = f"{title} {year} official trailer".strip()
    cache_key = query.lower()
    if cache_key in _yt_search_cache:
        return _yt_search_cache[cache_key]
    try:
        opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "default_search": "ytsearch",
            "playlist_items": "1",
            "socket_timeout": 10,
            "retries": 1,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
        if info and info.get("entries"):
            entry = info["entries"][0]
            key = entry.get("id")
            if key:
                _yt_search_cache[cache_key] = key
                return key
    except Exception:
        pass
    _yt_search_cache[cache_key] = None
    return None


def _format_currency(amount: int) -> str:
    if not amount or amount <= 0:
        return ""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount}"


_omdb_cache = {}


async def _fetch_omdb_ratings(imdb_id: str) -> dict:
    omdb_key = os.getenv("OMDB_API_KEY")
    if not omdb_key or not imdb_id:
        return {}
    if imdb_id in _omdb_cache:
        return _omdb_cache[imdb_id]
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.omdbapi.com/",
                params={"i": imdb_id, "apikey": omdb_key},
                timeout=10,
            )
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("Response") != "True":
            return {}
        ratings = {"imdb": {}, "rotten_tomatoes": {}, "metacritic": {}}
        if data.get("imdbRating") and data["imdbRating"] != "N/A":
            ratings["imdb"] = {"rating": float(data["imdbRating"]), "votes": data.get("imdbVotes", "").replace(",", "")}
        for r in data.get("Ratings", []):
            if r["Source"] == "Rotten Tomatoes":
                val = r["Value"].replace("%", "")
                ratings["rotten_tomatoes"] = {"tomatometer": int(val) if val.isdigit() else None, "value": r["Value"]}
            elif r["Source"] == "Metacritic":
                val = r["Value"].split("/")[0]
                ratings["metacritic"] = {"score": int(val) if val.isdigit() else None, "value": r["Value"]}
        _omdb_cache[imdb_id] = ratings
        return ratings
    except Exception:
        return {}


async def get_movie_detail(movie_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/movie/{movie_id}",
            params={"api_key": TMDB_KEY, "append_to_response": "videos,credits,similar,watch/providers,external_ids,release_dates"},
        )
    movie = resp.json()
    formatted = format_movie(movie)
    formatted["tagline"] = movie.get("tagline", "")
    formatted["runtime"] = movie.get("runtime", 0)
    formatted["status"] = movie.get("status", "")
    formatted["budget"] = movie.get("budget", 0)
    formatted["budget_formatted"] = _format_currency(movie.get("budget", 0))
    formatted["revenue"] = movie.get("revenue", 0)
    formatted["revenue_formatted"] = _format_currency(movie.get("revenue", 0))
    formatted["original_language"] = movie.get("original_language", "")
    formatted["original_title"] = movie.get("original_title", "")
    formatted["spoken_languages"] = [l["english_name"] for l in movie.get("spoken_languages", [])]
    formatted["production_companies"] = [
        {"name": c["name"], "logo": f"{IMG_BASE}/w92{c['logo_path']}" if c.get("logo_path") else None, "origin_country": c.get("origin_country", "")}
        for c in movie.get("production_companies", [])[:5]
    ]
    formatted["production_countries"] = [c["name"] for c in movie.get("production_countries", [])]
    formatted["homepage"] = movie.get("homepage", "")
    ext = movie.get("external_ids", {})
    formatted["external_ids"] = {
        "imdb": ext.get("imdb_id"),
        "facebook": ext.get("facebook_id"),
        "twitter": ext.get("twitter_id"),
        "instagram": ext.get("instagram_id"),
    }
    formatted["imdb_id"] = ext.get("imdb_id")
    formatted["imdb_url"] = f"https://www.imdb.com/title/{ext['imdb_id']}" if ext.get("imdb_id") else None
    formatted["tmdb_rating"] = movie.get("vote_average", 0)
    formatted["tmdb_votes"] = movie.get("vote_count", 0)
    omdb_ratings = await _fetch_omdb_ratings(ext.get("imdb_id", ""))
    formatted["imdb_rating"] = omdb_ratings.get("imdb", {}).get("rating")
    formatted["imdb_votes"] = omdb_ratings.get("imdb", {}).get("votes")
    formatted["rt_tomatometer"] = omdb_ratings.get("rotten_tomatoes", {}).get("tomatometer")
    formatted["rt_value"] = omdb_ratings.get("rotten_tomatoes", {}).get("value")
    formatted["metacritic_score"] = omdb_ratings.get("metacritic", {}).get("score")
    formatted["metacritic_value"] = omdb_ratings.get("metacritic", {}).get("value")
    rd = movie.get("release_dates", {}).get("results", [])
    certification = ""
    us_releases = []
    for country in rd:
        if country.get("iso_3166_1") == "US":
            for release in country.get("release_dates", []):
                cert = release.get("certification", "")
                if cert and not certification:
                    certification = cert
                us_releases.append({
                    "type": release.get("type", 0),
                    "date": release.get("release_date", ""),
                    "note": release.get("note", ""),
                })
    formatted["certification"] = certification
    formatted["us_releases"] = us_releases
    trailer_key = _pick_best_trailer(movie.get("videos", {}).get("results", []))
    if not trailer_key:
        trailer_key = _search_yt_trailer(movie.get("title", ""), movie.get("release_date", "")[:4])
    formatted["trailer_key"] = trailer_key
    formatted["cast"] = [
        {
            "id": c["id"],
            "name": c["name"],
            "character": c["character"],
            "profile": f"{IMG_BASE}/w185{c['profile_path']}" if c.get("profile_path") else None,
        }
        for c in movie.get("credits", {}).get("cast", [])[:12]
    ]
    formatted["director"] = next(
        ({"id": c["id"], "name": c["name"]} for c in movie.get("credits", {}).get("crew", []) if c.get("job") == "Director"),
        None
    )
    formatted["similar"] = [format_movie(r) for r in movie.get("similar", {}).get("results", [])[:8]]
    slug = re.sub(r'[^a-z0-9-]', '', movie['title'].lower().replace(' ', '-'))
    formatted["justwatch_url"] = f"https://www.justwatch.com/pk/movie/{slug}"
    
    providers = movie.get("watch/providers", {}).get("results", {})
    all_regions = {}
    for region_code, region_data in providers.items():
        if region_data.get("flatrate") or region_data.get("rent") or region_data.get("buy"):
            all_regions[region_code] = {
                "flatrate": [p["provider_name"] for p in region_data.get("flatrate", [])],
                "rent": [p["provider_name"] for p in region_data.get("rent", [])],
                "buy": [p["provider_name"] for p in region_data.get("buy", [])],
            }
    pk_providers = providers.get("PK", {})
    formatted["watch_providers"] = {
        "flatrate": [
            {"name": p["provider_name"], "logo": f"{IMG_BASE}/w92{p['logo_path']}" if p.get("logo_path") else None}
            for p in pk_providers.get("flatrate", [])
        ],
        "rent": [
            {"name": p["provider_name"], "logo": f"{IMG_BASE}/w92{p['logo_path']}" if p.get("logo_path") else None}
            for p in pk_providers.get("rent", [])
        ],
        "buy": [
            {"name": p["provider_name"], "logo": f"{IMG_BASE}/w92{p['logo_path']}" if p.get("logo_path") else None}
            for p in pk_providers.get("buy", [])
        ],
    }
    return formatted


# --- TV ---

async def get_tv_detail(tv_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/tv/{tv_id}",
            params={"api_key": TMDB_KEY, "append_to_response": "videos,credits,similar,watch/providers,external_ids,content_ratings"},
        )
    tv = resp.json()
    formatted = format_tv(tv)
    formatted["tagline"] = tv.get("tagline", "")
    formatted["status"] = tv.get("status", "")
    formatted["number_of_seasons"] = tv.get("number_of_seasons", 0)
    formatted["number_of_episodes"] = tv.get("number_of_episodes", 0)
    ext = tv.get("external_ids", {})
    formatted["external_ids"] = {
        "imdb": ext.get("imdb_id"),
        "facebook": ext.get("facebook_id"),
        "twitter": ext.get("twitter_id"),
        "instagram": ext.get("instagram_id"),
    }
    formatted["imdb_id"] = ext.get("imdb_id")
    formatted["imdb_url"] = f"https://www.imdb.com/title/{ext['imdb_id']}" if ext.get("imdb_id") else None
    formatted["tmdb_rating"] = tv.get("vote_average", 0)
    formatted["tmdb_votes"] = tv.get("vote_count", 0)
    cr = tv.get("content_ratings", {}).get("results", [])
    formatted["certification"] = next(
        (r["rating"] for r in cr if r.get("iso_3166_1") == "US"), ""
    )
    trailer_key = _pick_best_trailer(tv.get("videos", {}).get("results", []))
    if not trailer_key:
        trailer_key = _search_yt_trailer(tv.get("name", ""), tv.get("first_air_date", "")[:4])
    formatted["trailer_key"] = trailer_key
    formatted["cast"] = [
        {
            "id": c["id"],
            "name": c["name"],
            "character": c["character"],
            "profile": f"{IMG_BASE}/w185{c['profile_path']}" if c.get("profile_path") else None,
        }
        for c in tv.get("credits", {}).get("cast", [])[:12]
    ]
    formatted["similar"] = [format_tv(r) for r in tv.get("similar", {}).get("results", [])[:8]]
    return formatted


def format_person_credit(c: dict) -> dict:
    return {
        "id": c.get("id"),
        "title": c.get("title") or c.get("name", ""),
        "media_type": c.get("media_type", "movie"),
        "poster": f"{IMG_BASE}/w342{c.get('poster_path')}" if c.get("poster_path") else None,
        "year": (c.get("release_date") or c.get("first_air_date") or "")[:4],
        "character": c.get("character", ""),
        "rating": c.get("vote_average", 0),
        "overview": c.get("overview", ""),
    }


async def get_person_credits(person_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/person/{person_id}",
            params={
                "api_key": TMDB_KEY,
                "append_to_response": "movie_credits,tv_credits,external_ids",
            },
        )
    if resp.status_code != 200:
        return {"id": person_id, "name": "Unknown", "movie_credits": [], "tv_credits": []}

    data = resp.json()

    movies = []
    for c in data.get("movie_credits", {}).get("cast", []):
        movies.append(format_person_credit(c))

    tv = []
    for c in data.get("tv_credits", {}).get("cast", []):
        tv.append(format_person_credit(c))

    movies.sort(key=lambda x: -(x.get("rating") or 0))
    tv.sort(key=lambda x: -(x.get("rating") or 0))

    known_for = data.get("known_for_department", "")
    profile = data.get("profile_path")
    return {
        "id": data.get("id", person_id),
        "name": data.get("name", "Unknown"),
        "biography": data.get("biography", ""),
        "birthday": data.get("birthday"),
        "deathday": data.get("deathday"),
        "place_of_birth": data.get("place_of_birth"),
        "profile": f"{IMG_BASE}/w342{profile}" if profile else None,
        "known_for_department": known_for,
        "movie_credits": movies,
        "tv_credits": tv,
    }


# --- SEARCH ---

async def search_multi(query: str, page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/search/multi",
            params={"api_key": TMDB_KEY, "query": query, "page": page},
        )
    results = resp.json().get("results", [])
    formatted = []
    for r in results:
        if r.get("media_type") == "movie":
            formatted.append(format_movie(r))
        elif r.get("media_type") == "tv":
            formatted.append(format_tv(r))
    return formatted[:20]


async def search_movies(query: str, page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/search/movie",
            params={"api_key": TMDB_KEY, "query": query, "page": page},
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:12]]


async def get_genres() -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/genre/movie/list",
            params={"api_key": TMDB_KEY},
        )
    return resp.json().get("genres", [])


async def get_watch_providers(region: str = "PK") -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/watch/providers/movie",
            params={"api_key": TMDB_KEY, "watch_region": region},
        )
    return resp.json().get("results", [])[:20]


async def get_tv_seasons(tv_id: int) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/tv/{tv_id}",
            params={"api_key": TMDB_KEY},
        )
    tv = resp.json()
    seasons = tv.get("seasons", [])
    result = []
    for s in seasons:
        if s.get("season_number", 0) == 0:
            continue
        result.append({
            "season_number": s["season_number"],
            "episode_count": s.get("episode_count", 0),
            "name": s.get("name", f"Season {s['season_number']}"),
            "poster": f"{IMG_BASE}/w342{s['poster_path']}" if s.get("poster_path") else None,
        })
    return result


async def get_tv_episodes(tv_id: int, season_number: int) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/tv/{tv_id}/season/{season_number}",
            params={"api_key": TMDB_KEY},
        )
    season = resp.json()
    episodes = season.get("episodes", [])
    return [
        {
            "id": e["id"],
            "episode_number": e["episode_number"],
            "name": e.get("name", f"Episode {e['episode_number']}"),
            "overview": e.get("overview", ""),
            "still": f"{IMG_BASE}/w300{e['still_path']}" if e.get("still_path") else None,
            "rating": e.get("vote_average", 0),
        }
        for e in episodes
    ]


async def discover_movies(page: int = 1, sort_by: str = "popularity.desc", genre_id: int = None) -> list:
    params = {
        "api_key": TMDB_KEY,
        "page": page,
        "sort_by": sort_by,
        "vote_count.gte": 50,
        "primary_release_date.lte": _today(),
    }
    if genre_id:
        params["with_genres"] = str(genre_id)
    if sort_by == "primary_release_date.desc":
        params["primary_release_date.gte"] = "2024-01-01"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/discover/movie", params=params)
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


async def get_now_playing_movies(page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/movie/now_playing",
            params={
                "api_key": TMDB_KEY,
                "language": "en-US",
                "page": page,
                "region": "US",
            },
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


async def get_upcoming_movies(page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/discover/movie",
            params={
                "api_key": TMDB_KEY,
                "sort_by": "primary_release_date.asc",
                "primary_release_date.gte": _today(),
                "page": page,
            },
        )
    return [format_movie(m) for m in resp.json().get("results", [])[:20]]


async def get_by_provider(provider_id: int, page: int = None) -> list:
    if page is None:
        page = 1
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/discover/movie",
            params={
                "api_key": TMDB_KEY,
                "with_watch_providers": provider_id,
                "watch_region": "US",
                "sort_by": "popularity.desc",
                "vote_count.gte": 50,
                "page": page,
            },
        )
    results = resp.json().get("results", [])
    return [format_movie(m) for m in results[:20]]



