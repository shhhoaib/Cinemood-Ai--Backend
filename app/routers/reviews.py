import json
import os
import uuid
import time
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from app.routers.users import _load_users, _get_current_user

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")
os.makedirs(DATA_DIR, exist_ok=True)


def _reviews_path():
    return os.path.join(DATA_DIR, "_reviews.json")


def _load_reviews():
    p = _reviews_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_reviews(reviews):
    with open(_reviews_path(), "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2)


class ReviewCreate(BaseModel):
    movie_id: Optional[int] = None
    tv_id: Optional[int] = None
    text: str
    parent_id: Optional[str] = None


class ReviewUpdate(BaseModel):
    text: str


@router.post("/reviews")
async def create_review(body: ReviewCreate, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    content_id = body.movie_id or body.tv_id
    content_type = "movie" if body.movie_id else "tv"
    if not content_id:
        raise HTTPException(status_code=400, detail="movie_id or tv_id required")
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if body.parent_id:
        all_reviews = _load_reviews()
        parent_found = False
        for cid, reviews in all_reviews.items():
            for r in reviews:
                if r["id"] == body.parent_id:
                    parent_found = True
                    break
            if parent_found:
                break
        if not parent_found:
            raise HTTPException(status_code=404, detail="Parent review not found")

    review = {
        "id": str(uuid.uuid4()),
        "content_type": content_type,
        "content_id": content_id,
        "user_id": user["id"],
        "user_name": user.get("name", "User"),
        "text": body.text.strip(),
        "parent_id": body.parent_id,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "likes": 0,
    }

    all_reviews = _load_reviews()
    key = f"{content_type}_{content_id}"
    if key not in all_reviews:
        all_reviews[key] = []
    all_reviews[key].append(review)
    _save_reviews(all_reviews)

    return {"review": review}


@router.get("/reviews/{content_type}/{content_id}")
async def get_reviews(content_type: str, content_id: int):
    all_reviews = _load_reviews()
    key = f"{content_type}_{content_id}"
    reviews = all_reviews.get(key, [])
    reviews.sort(key=lambda r: r["created_at"], reverse=True)

    top = [r for r in reviews if not r.get("parent_id")]
    replies_map = {}
    for r in reviews:
        pid = r.get("parent_id")
        if pid:
            if pid not in replies_map:
                replies_map[pid] = []
            replies_map[pid].append(r)

    for t in top:
        t["replies"] = sorted(replies_map.get(t["id"], []), key=lambda r: r["created_at"])

    return {"reviews": top, "total": len(reviews)}


@router.put("/reviews/{review_id}")
async def update_review(review_id: str, body: ReviewUpdate, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    all_reviews = _load_reviews()
    for key, reviews in all_reviews.items():
        for i, r in enumerate(reviews):
            if r["id"] == review_id:
                if r["user_id"] != user["id"]:
                    raise HTTPException(status_code=403, detail="Not your review")
                all_reviews[key][i]["text"] = body.text.strip()
                all_reviews[key][i]["updated_at"] = int(time.time())
                _save_reviews(all_reviews)
                return {"review": all_reviews[key][i]}

    raise HTTPException(status_code=404, detail="Review not found")


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    all_reviews = _load_reviews()
    for key, reviews in list(all_reviews.items()):
        all_reviews[key] = [r for r in reviews if r["id"] != review_id and r.get("parent_id") != review_id]
        if not all_reviews[key]:
            del all_reviews[key]

    _save_reviews(all_reviews)
    return {"status": "deleted"}


@router.post("/reviews/{review_id}/like")
async def like_review(review_id: str, authorization: str = Header(None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    all_reviews = _load_reviews()
    for key, reviews in all_reviews.items():
        for i, r in enumerate(reviews):
            if r["id"] == review_id:
                all_reviews[key][i]["likes"] = r.get("likes", 0) + 1
                _save_reviews(all_reviews)
                return {"likes": all_reviews[key][i]["likes"]}

    raise HTTPException(status_code=404, detail="Review not found")
