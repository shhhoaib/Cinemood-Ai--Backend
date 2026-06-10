import json
import os
import time
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional

from app.routers.users import _get_current_user

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")
os.makedirs(DATA_DIR, exist_ok=True)


def _ratings_path():
    return os.path.join(DATA_DIR, "_ratings.json")


def _load_ratings():
    p = _ratings_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_ratings(ratings):
    with open(_ratings_path(), "w", encoding="utf-8") as f:
        json.dump(ratings, f, indent=2)


def get_content_rating_stats(content_type: str, content_id: int):
    ratings = _load_ratings()
    key = f"{content_type}_{content_id}"
    content_ratings = ratings.get(key, {})
    values = [v for v in content_ratings.values() if isinstance(v, (int, float))]
    count = len(values)
    if count == 0:
        return {"average": None, "count": 0, "distribution": {}}
    dist = {}
    for v in values:
        dist[v] = dist.get(v, 0) + 1
    return {
        "average": round(sum(values) / count, 1),
        "count": count,
        "distribution": dict(sorted(dist.items())),
    }


class RatingSubmit(BaseModel):
    movie_id: Optional[int] = None
    tv_id: Optional[int] = None
    rating: int


@router.post("/ratings")
async def submit_rating(body: RatingSubmit, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if body.rating < 1 or body.rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be 1-10")

    content_id = body.movie_id or body.tv_id
    content_type = "movie" if body.movie_id else "tv"
    if not content_id:
        raise HTTPException(status_code=400, detail="movie_id or tv_id required")

    ratings = _load_ratings()
    key = f"{content_type}_{content_id}"
    if key not in ratings:
        ratings[key] = {}
    ratings[key][user["id"]] = body.rating
    _save_ratings(ratings)

    stats = get_content_rating_stats(content_type, content_id)
    return {"user_rating": body.rating, **stats}


@router.get("/ratings/{content_type}/{content_id}")
async def get_ratings(content_type: str, content_id: int, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    stats = get_content_rating_stats(content_type, content_id)
    result = {**stats}
    if user:
        ratings = _load_ratings()
        key = f"{content_type}_{content_id}"
        result["user_rating"] = ratings.get(key, {}).get(user["id"])
    return result
