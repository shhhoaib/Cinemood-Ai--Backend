from fastapi import APIRouter, Query, HTTPException
from app.services.tmdb import (
    get_trending_movies,
    get_trending_tv,
    get_popular_movies,
    get_popular_tv,
    get_top_rated_movies,
    get_movie_detail,
    get_tv_detail,
    get_by_genre,
    search_movies,
    search_multi,
    get_genres,
    get_watch_providers,
    get_by_provider,
    get_tv_seasons,
    get_tv_episodes,
    discover_movies,
    get_now_playing_movies,
    get_upcoming_movies,
)
from app.services.tmdb import INDUSTRIES, get_by_industry, get_person_credits
from app.services.gemini import analyze_movie_emotions

router = APIRouter()


@router.get("/trending")
async def trending():
    try:
        movies = await get_trending_movies()
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending/tv")
async def trending_tv():
    try:
        shows = await get_trending_tv()
        return {"movies": shows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def popular(page: int = Query(1, ge=1)):
    try:
        movies = await get_popular_movies(page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular/tv")
async def popular_tv(page: int = Query(1, ge=1)):
    try:
        shows = await get_popular_tv(page)
        return {"movies": shows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-rated")
async def top_rated(page: int = Query(1, ge=1)):
    try:
        movies = await get_top_rated_movies(page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/now-playing")
async def now_playing(page: int = Query(1, ge=1)):
    try:
        movies = await get_now_playing_movies(page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def upcoming(page: int = Query(1, ge=1)):
    try:
        movies = await get_upcoming_movies(page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover")
async def discover(
    page: int = Query(1, ge=1),
    sort_by: str = Query("popularity.desc"),
    genre_id: int = Query(None),
):
    try:
        movies = await discover_movies(page, sort_by, genre_id)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genre/{genre_id}")
async def by_genre(genre_id: int, page: int = Query(1, ge=1)):
    try:
        movies = await get_by_genre(genre_id, page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{movie_id}")
async def movie_detail(movie_id: int):
    try:
        movie = await get_movie_detail(movie_id)
        return {"movie": movie}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mood-profile/{movie_id}")
async def movie_mood_profile(movie_id: int):
    try:
        from app.services.tmdb import get_movie_detail as _detail
        movie = await _detail(movie_id)
        emotions = await analyze_movie_emotions(
            movie.get("title", ""),
            movie.get("overview", ""),
            movie.get("genre_names", []),
        )
        return {"emotional_profile": emotions, "movie_id": movie_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tv/detail/{tv_id}")
async def tv_detail(tv_id: int):
    try:
        tv = await get_tv_detail(tv_id)
        return {"movie": tv}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(query: str = Query(..., min_length=1), page: int = Query(1, ge=1)):
    try:
        movies = await search_movies(query, page)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/multi")
async def search_multi_endpoint(query: str = Query(..., min_length=1), page: int = Query(1, ge=1)):
    try:
        results = await search_multi(query, page)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/genres")
async def genres():
    try:
        genre_list = await get_genres()
        return {"genres": genre_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def watch_providers(region: str = Query("PK")):
    try:
        providers = await get_watch_providers(region)
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tv/{tv_id}/seasons")
async def tv_seasons(tv_id: int):
    try:
        seasons = await get_tv_seasons(tv_id)
        return {"seasons": seasons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tv/{tv_id}/season/{season_number}")
async def tv_episodes(tv_id: int, season_number: int):
    try:
        episodes = await get_tv_episodes(tv_id, season_number)
        return {"episodes": episodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaming/{provider_id}")
async def by_streaming(provider_id: int):
    try:
        movies = await get_by_provider(provider_id)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


PROVIDERS = {
    "netflix": 8,
    "prime": 9,
    "disney": 337,
    "apple": 350,
    "hulu": 15,
}


@router.get("/providers/trending")
async def providers_trending():
    try:
        import asyncio
        results = {}
        async def fetch(name, pid):
            movies = await get_by_provider(pid)
            results[name] = movies
        tasks = [fetch(name, pid) for name, pid in PROVIDERS.items()]
        await asyncio.gather(*tasks)
        return {"providers": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industries")
async def list_industries():
    try:
        result = [
            {"id": k, **v}
            for k, v in INDUSTRIES.items()
        ]
        return {"industries": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/person/{person_id}")
async def person_detail(person_id: int):
    try:
        data = await get_person_credits(person_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry/{industry_id}")
async def industry_movies(
    industry_id: str,
    page: int = Query(1, ge=1),
    subcategory: str = Query(None),
    media_type: str = Query("movie"),
    watch_provider: str = Query(None),
):
    try:
        movies = await get_by_industry(industry_id, page, subcategory, media_type, watch_provider)
        return {"movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
