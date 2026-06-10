from fastapi import APIRouter, Query, HTTPException, Body
from app.services.user_profile import track_watch, track_like, track_rating, track_search, get_profile
from app.services.recommendation_engine import hybrid_recommendations, dna_recommendations, dna_recommendations_page, compute_user_genre_vector
from app.services.tmdb import discover_movies, get_movie_detail, get_tv_detail

router = APIRouter()


@router.post("/recommend/track/watch")
async def api_track_watch(data: dict = Body(...)):
    try:
        track_watch(
            user_id=data.get("user_id", "default"),
            media_id=data["media_id"],
            media_type=data.get("media_type", "movie"),
            title=data.get("title", ""),
            genres=data.get("genres", []),
            watch_pct=data.get("watch_pct", 0),
            completed=data.get("completed", False),
            rewatch=data.get("rewatch", False),
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/track/like")
async def api_track_like(data: dict = Body(...)):
    try:
        track_like(
            user_id=data.get("user_id", "default"),
            media_id=data["media_id"],
            media_type=data.get("media_type", "movie"),
            liked=data.get("liked", True),
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/track/rating")
async def api_track_rating(data: dict = Body(...)):
    try:
        track_rating(
            user_id=data.get("user_id", "default"),
            media_id=data["media_id"],
            media_type=data.get("media_type", "movie"),
            rating=data.get("rating", 0),
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/track/search")
async def api_track_search(data: dict = Body(...)):
    try:
        track_search(
            user_id=data.get("user_id", "default"),
            query=data.get("query", ""),
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/for-you")
async def recommend_for_you(user_id: str = Query("default"), page: int = Query(1, ge=1)):
    try:
        from app.services.tmdb import discover_movies, get_by_genre
        from app.services.user_profile import get_profile as _get_profile

        profile = _get_profile(user_id)
        has_history = len(profile.get("watched", [])) > 0

        if has_history:
            # Use hybrid engine for users with watch history
            all_movies = []
            for p in range(1, 4):
                batch = await discover_movies(page=p, sort_by="popularity.desc")
                all_movies.extend(batch)
            for gid in [28, 35, 18, 10749, 27]:
                batch = await get_by_genre(gid, page=1)
                all_movies.extend(batch)

            seen = set()
            unique = []
            for m in all_movies:
                mid = m.get("id")
                if mid not in seen:
                    seen.add(mid)
                    unique.append(m)

            recs = hybrid_recommendations(user_id, unique, top_n=24)
        else:
            # Use DNA-based recommendations for new users
            recs = await dna_recommendations(user_id, top_n=24)

        start = (page - 1) * 20
        end = start + 20
        page_recs = recs[start:end]

        return {
            "recommendations": page_recs,
            "total": len(recs),
            "page": page,
            "source": "history" if has_history else "dna",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/dna-picks/{user_id}")
async def recommend_dna_picks(user_id: str, page: int = Query(1, ge=1)):
    try:
        recs = await dna_recommendations_page(user_id, page=page, per_page=20)
        return {
            "recommendations": recs,
            "page": page,
            "source": "dna",
            "has_more": len(recs) == 20,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/profile")
async def get_user_profile(user_id: str = Query("default")):
    try:
        profile = get_profile(user_id)
        genre_vec = compute_user_genre_vector(user_id)
        genre_keys = [
            "action", "adventure", "animation", "comedy", "crime",
            "documentary", "drama", "family", "fantasy", "history",
            "horror", "music", "mystery", "romance", "sci-fi",
            "tv movie", "thriller", "war", "western", "action adventure",
            "sci-fi fantasy",
        ]
        top_genres = sorted(
            [(genre_keys[i] if i < len(genre_keys) else f"genre_{i}", float(v)) for i, v in enumerate(genre_vec) if v > 0],
            key=lambda x: -x[1],
        )[:5]
        return {
            "profile": {
                "total_watched": len(profile.get("watched", [])),
                "total_likes": len(profile.get("likes", [])),
                "total_dislikes": len(profile.get("dislikes", [])),
                "total_searches": len(profile.get("searches", [])),
                "top_genres": top_genres,
                "watch_time_minutes": profile.get("session", {}).get("total_watch_time", 0),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
