import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from functools import lru_cache
import time

import httpx
from app.services.tmdb import TMDB_KEY, BASE_URL
from app.services.user_profile import get_profile, get_all_users

TMDB_GENRES = {
    28: "action", 12: "adventure", 16: "animation", 35: "comedy", 80: "crime",
    99: "documentary", 18: "drama", 10751: "family", 14: "fantasy", 36: "history",
    27: "horror", 10402: "music", 9648: "mystery", 10749: "romance",
    878: "sci-fi", 10770: "tv movie", 53: "thriller", 10752: "war", 37: "western",
    10759: "action adventure", 10765: "sci-fi fantasy",
}


def _genre_vector(genre_ids):
    vec = [0] * len(TMDB_GENRES)
    for gid in genre_ids:
        keys = list(TMDB_GENRES.keys())
        if gid in keys:
            vec[keys.index(gid)] = 1
    return vec


def build_content_profile(movie):
    genre_ids = movie.get("genre_ids", []) or []
    title = movie.get("title", "") or movie.get("name", "")
    overview = movie.get("overview", "") or ""
    return f"{title} {' '.join(TMDB_GENRES.get(g, '') for g in genre_ids)} {overview[:200]}"


def compute_user_genre_vector(user_id: str) -> np.ndarray:
    profile = get_profile(user_id)
    vec = np.zeros(len(TMDB_GENRES))
    for w in profile.get("watched", []):
        gids = w.get("genres", [])
        weight = 1.0
        if w.get("completed"):
            weight = 2.0
        if w.get("rewatch_count", 0) > 1:
            weight *= 1.5
        keys = list(TMDB_GENRES.keys())
        for gid in gids:
            if gid in keys:
                vec[keys.index(gid)] += weight
    for l in profile.get("likes", []):
        vec += 0.5
    for d in profile.get("dislikes", []):
        vec -= 0.5
    vec = np.maximum(vec, 0)
    if vec.sum() > 0:
        vec = vec / vec.sum()
    return vec


def compute_item_similarity(movie_a: dict, movie_b: dict) -> float:
    va = _genre_vector(movie_a.get("genre_ids", []) or [])
    vb = _genre_vector(movie_b.get("genre_ids", []) or [])
    if sum(va) == 0 or sum(vb) == 0:
        return 0.0
    return float(cosine_similarity([va], [vb])[0][0])


@lru_cache(maxsize=1)
def _get_tfidf_matrix(movies_tuple):
    docs = [build_content_profile(m) for m in movies_tuple]
    if not docs:
        return None, None
    vec = TfidfVectorizer(max_features=500, stop_words="english")
    mat = vec.fit_transform(docs)
    return vec, mat


def content_based_recommendations(user_id: str, all_movies: list, top_n: int = 20) -> list:
    profile = get_profile(user_id)
    watched = profile.get("watched", [])
    if not watched:
        return []

    watched_ids = {(w["media_id"], w["media_type"]) for w in watched}
    unwatched = [m for m in all_movies if (m.get("id"), m.get("media_type", "movie")) not in watched_ids]
    if not unwatched:
        return []

    user_vec = compute_user_genre_vector(user_id)
    scored = []
    for m in unwatched:
        m_vec = _genre_vector(m.get("genre_ids", []) or [])
        genre_score = float(np.dot(user_vec, m_vec))
        scored.append((genre_score, m))

    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_n]]


def collaborative_recommendations(user_id: str, all_movies: list, top_n: int = 20) -> list:
    profiles = get_all_users()
    if len(profiles) < 2:
        return []

    target = get_profile(user_id)
    target_watched = {(w["media_id"], w["media_type"]) for w in target.get("watched", [])}
    if not target_watched:
        return []

    user_genre_vecs = {}
    for uid, p in profiles.items():
        vec = np.zeros(len(TMDB_GENRES))
        for w in p.get("watched", []):
            gids = w.get("genres", [])
            keys = list(TMDB_GENRES.keys())
            for gid in gids:
                if gid in keys:
                    vec[keys.index(gid)] += 1
        if vec.sum() > 0:
            vec = vec / vec.sum()
        user_genre_vecs[uid] = vec

    target_vec = user_genre_vecs.get(user_id)
    if target_vec is None or target_vec.sum() == 0:
        return []

    similarities = []
    for uid, vec in user_genre_vecs.items():
        if uid == user_id:
            continue
        sim = cosine_similarity([target_vec], [vec])[0][0]
        similarities.append((sim, uid))

    similarities.sort(key=lambda x: -x[0])
    similar_users = [s for s in similarities[:5] if s[0] > 0.1]

    rec_scores = defaultdict(float)
    for sim_score, uid in similar_users:
        p = profiles[uid]
        for w in p.get("watched", []):
            mid = (w["media_id"], w["media_type"])
            if mid in target_watched:
                continue
            weight = sim_score
            if w.get("completed"):
                weight *= 1.5
            rec_scores[mid] += weight

    unwatched_map = {}
    for m in all_movies:
        unwatched_map[(m.get("id"), m.get("media_type", "movie"))] = m

    scored = []
    for mid, score in rec_scores.items():
        if mid in unwatched_map:
            scored.append((score, unwatched_map[mid]))

    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_n]]


from collections import defaultdict
from app.services.user_dna import DNA_ARCHETYPES


def hybrid_recommendations(user_id: str, all_movies: list, top_n: int = 24) -> list:
    profile = get_profile(user_id)
    watched_ids = {(w["media_id"], w["media_type"]) for w in profile.get("watched", [])}

    content_recs = content_based_recommendations(user_id, all_movies, top_n * 2)
    collab_recs = collaborative_recommendations(user_id, all_movies, top_n * 2)

    seen = set()
    scored = []

    # Scoring formula: 40% engagement + 25% collaborative + 15% content + 10% sequential + 10% popularity
    user_genre_vec = compute_user_genre_vector(user_id)

    for m in all_movies:
        mid = (m.get("id"), m.get("media_type", "movie"))
        if mid in watched_ids:
            continue
        if mid in seen:
            continue
        seen.add(mid)

        score = 0.0

        # Engagement signals (40%)
        m_vec = _genre_vector(m.get("genre_ids", []) or [])
        engagement = float(np.dot(user_genre_vec, m_vec)) * 0.4
        score += engagement

        # Content similarity (15%) - boosted if in content recs
        content_boost = 0.15 if m in content_recs else 0.0
        score += content_boost

        # Collaborative (25%) - boosted if in collab recs
        collab_boost = 0.25 if m in collab_recs else 0.0
        score += collab_boost

        # Popularity signal (10%)
        pop = m.get("vote_average", 0) / 10.0
        score += pop * 0.10

        # Sequential recency (10%) - prefer newer content
        year = m.get("year") or m.get("release_date", "")[:4]
        if year and year.isdigit():
            y = int(year)
            recency = min((y - 2020) / 6.0, 1.0) if y >= 2020 else 0.0
            score += recency * 0.10

        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_n]]


def get_dna_archetype_ids(user_id: str) -> list:
    from app.services.user_profile import get_profile as _get_profile
    profile = _get_profile(user_id)
    fav_genres = profile.get("favorite_genres", [])
    watched = profile.get("watched", [])

    watched_genres = {}
    for w in watched:
        for g in w.get("genres", []):
            watched_genres[g] = watched_genres.get(g, 0) + 1

    combined = {}
    for g in fav_genres:
        gid = int(g) if isinstance(g, str) else g
        combined[gid] = combined.get(gid, 0) + 5
    for gid, cnt in watched_genres.items():
        combined[gid] = combined.get(gid, 0) + cnt

    top_ids = [gid for gid, _ in sorted(combined.items(), key=lambda x: -x[1])[:5]]

    # Score each archetype and find the primary one
    arch_scores = []
    for arch in DNA_ARCHETYPES:
        score = 0
        for g in top_ids:
            if g in arch.get("genres", []):
                score += 2
        for g in fav_genres:
            gid = int(g) if isinstance(g, str) else g
            if gid in arch.get("genres", []):
                score += 3
        arch_scores.append((score, arch))

    arch_scores.sort(key=lambda x: -x[0])
    primary = arch_scores[0][1] if arch_scores else None

    # Use primary archetype genres + favorite genres
    result = set(primary.get("genres", [])) if primary else set()
    for g in fav_genres:
        gid = int(g) if isinstance(g, str) else g
        result.add(gid)

    fallback = list(result) if result else [28, 878, 12]
    return fallback[:8]


async def dna_recommendations(user_id: str, top_n: int = 24) -> list:
    from app.services.tmdb import discover_movies, get_by_genre, format_movie
    from app.services.user_profile import get_profile as _get_profile

    profile = _get_profile(user_id)
    fav_actors = profile.get("favorite_actors", [])
    fav_directors = profile.get("favorite_directors", [])
    fav_genres = profile.get("favorite_genres", [])

    genre_ids = get_dna_archetype_ids(user_id)

    seen = set()
    results = []

    # 1. Fetch movies by DNA genre IDs
    for gid in genre_ids[:5]:
        for p in [1, 2]:
            if len(results) >= top_n * 3:
                break
            batch = await get_by_genre(gid, page=p)
            for m in batch:
                mid = m.get("id")
                if mid not in seen:
                    seen.add(mid)
                    results.append(m)

    # 2. Also fetch general popular/trending
    if len(results) < top_n:
        for p in [1, 2]:
            batch = await discover_movies(page=p, sort_by="popularity.desc")
            for m in batch:
                mid = m.get("id")
                if mid not in seen:
                    seen.add(mid)
                    results.append(m)

    if not results:
        return []

    watched = profile.get("watched", [])
    watched_ids = {(w["media_id"], w.get("media_type", "movie")) for w in watched}

    scored = []
    for m in results:
        mid = (m.get("id"), "movie")
        if mid in watched_ids:
            continue

        score = 0.0

        m_genres = set(m.get("genre_ids", []) or [])
        genre_hits = sum(1 for g in m_genres if g in genre_ids)
        score += (genre_hits / max(len(genre_ids), 1)) * 0.6

        for arch in DNA_ARCHETYPES:
            arch_match = sum(1 for g in m_genres if g in arch.get("genres", []))
            if arch_match >= 2:
                score += 0.15
                break

        title = (m.get("title") or "").lower()
        for actor in fav_actors:
            if actor.lower() in title:
                score += 0.10
                break
        for director in fav_directors:
            if director.lower() in title:
                score += 0.10
                break

        pop = m.get("vote_average", 0) / 10.0
        score += pop * 0.10

        year = m.get("year") or (m.get("release_date") or "")[:4]
        if year and str(year).isdigit():
            y = int(year)
            recency = min((y - 2020) / 6.0, 1.0) if y >= 2020 else 0.0
            score += recency * 0.05

        scored.append((score, m))

    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:top_n]]


async def dna_recommendations_page(user_id: str, page: int = 1, per_page: int = 20) -> list:
    from app.services.tmdb import discover_movies, format_movie
    from app.services.user_profile import get_profile as _get_profile

    profile = _get_profile(user_id)
    genre_ids = get_dna_archetype_ids(user_id)

    if not genre_ids:
        genre_ids = [28, 878, 12]

    genre_str = ",".join(str(g) for g in genre_ids[:3])

    params = {
        "with_genres": genre_str,
        "sort_by": "popularity.desc",
        "vote_count.gte": 20,
        "page": page,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/discover/movie",
            params={"api_key": TMDB_KEY, **params},
        )
    results = resp.json().get("results", [])

    watched = profile.get("watched", [])
    watched_ids = {w["media_id"] for w in watched}

    movies = []
    for m in results:
        if m.get("id") in watched_ids:
            continue
        movies.append(format_movie(m))

    return movies
