import json
import os
import time
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")
os.makedirs(DATA_DIR, exist_ok=True)


def _path(user_id):
    return os.path.join(DATA_DIR, f"user_{user_id}.json")


def _load(user_id):
    p = _path(user_id)
    if not os.path.exists(p):
        return _default()
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(user_id, data):
    with open(_path(user_id), "w") as f:
        json.dump(data, f, indent=2)


def _default():
    return {
        "name": "",
        "email": "",
        "age": 25,
        "favorite_genres": [],
        "favorite_actors": [],
        "favorite_actresses": [],
        "favorite_directors": [],
        "favorite_writers": [],
        "bio": "",
        "created_at": None,
        "updated_at": None,
        "watched": [],
        "likes": [],
        "dislikes": [],
        "ratings": [],
        "searches": [],
        "genre_views": defaultdict(int),
        "session": {"total_watch_time": 0, "episodes_watched": 0, "last_active": 0},
    }


def track_watch(user_id: str, media_id: int, media_type: str, title: str, genres: list, watch_pct: float, completed: bool, rewatch: bool = False):
    data = _load(user_id)
    entry = {
        "media_id": media_id,
        "media_type": media_type,
        "title": title,
        "genres": genres,
        "watch_pct": watch_pct,
        "completed": completed,
        "timestamp": time.time(),
        "rewatch": rewatch,
    }
    if rewatch:
        existing = [w for w in data["watched"] if w["media_id"] == media_id and w["media_type"] == media_type]
        for e in existing:
            e["rewatch_count"] = e.get("rewatch_count", 1) + 1
    else:
        data["watched"].append(entry)
    for g in genres:
        data["genre_views"][str(g)] += 1
    data["session"]["total_watch_time"] += watch_pct * 2  # approximate minutes
    data["session"]["episodes_watched"] += 1
    data["session"]["last_active"] = time.time()
    _save(user_id, data)


def track_like(user_id: str, media_id: int, media_type: str, liked: bool):
    data = _load(user_id)
    if liked:
        if media_id not in data["likes"]:
            data["likes"].append({"media_id": media_id, "media_type": media_type, "timestamp": time.time()})
        data["dislikes"] = [d for d in data["dislikes"] if d["media_id"] != media_id]
    else:
        if media_id not in data["dislikes"]:
            data["dislikes"].append({"media_id": media_id, "media_type": media_type, "timestamp": time.time()})
        data["likes"] = [l for l in data["likes"] if l["media_id"] != media_id]
    data["session"]["last_active"] = time.time()
    _save(user_id, data)


def track_rating(user_id: str, media_id: int, media_type: str, rating: float):
    data = _load(user_id)
    existing = [r for r in data["ratings"] if r["media_id"] == media_id]
    if existing:
        existing[0]["rating"] = rating
        existing[0]["timestamp"] = time.time()
    else:
        data["ratings"].append({"media_id": media_id, "media_type": media_type, "rating": rating, "timestamp": time.time()})
    data["session"]["last_active"] = time.time()
    _save(user_id, data)


def track_search(user_id: str, query: str):
    data = _load(user_id)
    data["searches"].append({"query": query, "timestamp": time.time()})
    data["session"]["last_active"] = time.time()
    _save(user_id, data)


def get_profile(user_id: str) -> dict:
    return _load(user_id)


def get_all_users():
    profiles = {}
    for f in os.listdir(DATA_DIR):
        if f.startswith("user_") and f.endswith(".json"):
            uid = f.replace("user_", "").replace(".json", "")
            profiles[uid] = _load(uid)
    return profiles
