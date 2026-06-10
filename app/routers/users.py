import json
import os
import uuid
import time
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import bcrypt as _bcrypt
from jose import jwt, JWTError

from app.services.user_profile import _load as _load_profile, _save as _save_profile, _default as _default_profile
from app.services.user_dna import analyze_user_dna

router = APIRouter()

SECRET_KEY = os.environ.get("JWT_SECRET", "cinemood-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")
os.makedirs(DATA_DIR, exist_ok=True)


def _users_path():
    return os.path.join(DATA_DIR, "_users.json")


def _load_users():
    p = _users_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(users):
    with open(_users_path(), "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _user_registry_path():
    return os.path.join(DATA_DIR, "_user_registry.json")


def _load_registry():
    p = _user_registry_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(registry):
    with open(_user_registry_path(), "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _get_current_user(authorization: str):
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        users = _load_users()
        user = users.get(user_id)
        if not user:
            return None
        return {**user, "id": user_id}
    except JWTError:
        return None


# --- Models ---

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=6, max_length=100)
    age: int = Field(default=25, ge=5, le=120)
    favorite_genres: list = Field(default_factory=list, max_length=10)
    favorite_actors: list = Field(default_factory=list, max_length=10)
    favorite_actresses: list = Field(default_factory=list, max_length=10)
    favorite_directors: list = Field(default_factory=list, max_length=10)
    favorite_writers: list = Field(default_factory=list, max_length=10)
    bio: str = Field(default="", max_length=500)


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    favorite_genres: Optional[list] = None
    favorite_actors: Optional[list] = None
    favorite_actresses: Optional[list] = None
    favorite_directors: Optional[list] = None
    favorite_writers: Optional[list] = None
    bio: Optional[str] = None


# --- Endpoints ---

@router.post("/users/register")
async def register(req: RegisterRequest):
    import traceback
    try:
        users = _load_users()
        for uid, u in users.items():
            if u.get("email", "").lower() == req.email.lower():
                raise HTTPException(status_code=400, detail="Email already registered")
        user_id = str(uuid.uuid4())
        password_hash = _bcrypt.hashpw(req.password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
        now = time.time()
        users[user_id] = {
            "email": req.email.lower(),
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }
        _save_users(users)
        registry = _load_registry()
        registry[req.email.lower()] = user_id
        _save_registry(registry)
        profile = _default_profile()
        profile.update({
            "name": req.name,
            "email": req.email.lower(),
            "age": req.age,
            "favorite_genres": req.favorite_genres,
            "favorite_actors": req.favorite_actors,
            "favorite_actresses": req.favorite_actresses,
            "favorite_directors": req.favorite_directors,
            "favorite_writers": req.favorite_writers,
            "bio": req.bio,
            "created_at": now,
        })
        _save_profile(user_id, profile)
        dna = analyze_user_dna(profile)
        token = create_access_token(user_id)
        return {
            "token": token,
            "user": {
                "id": user_id,
                "name": req.name,
                "email": req.email.lower(),
                "age": req.age,
                "favorite_genres": req.favorite_genres,
                "favorite_actors": req.favorite_actors,
                "favorite_actresses": req.favorite_actresses,
                "favorite_directors": req.favorite_directors,
                "favorite_writers": req.favorite_writers,
                "bio": req.bio,
            },
            "dna": dna,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.post("/users/login")
async def login(req: LoginRequest):
    registry = _load_registry()
    email_lower = req.email.lower()
    user_id = registry.get(email_lower)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    users = _load_users()
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    try:
        valid = _bcrypt.checkpw(req.password.encode("utf-8"), user["password_hash"].encode("utf-8"))
    except Exception:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    profile = _load_profile(user_id)
    token = create_access_token(user_id)
    dna = analyze_user_dna(profile)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": profile.get("name", ""),
            "email": profile.get("email", email_lower),
            "age": profile.get("age", 25),
            "favorite_genres": profile.get("favorite_genres", []),
            "favorite_actors": profile.get("favorite_actors", []),
            "favorite_actresses": profile.get("favorite_actresses", []),
            "favorite_directors": profile.get("favorite_directors", []),
            "favorite_writers": profile.get("favorite_writers", []),
            "bio": profile.get("bio", ""),
        },
        "dna": dna,
    }


@router.get("/users/me")
async def get_me(current_user_id: str = Depends(get_current_user)):
    profile = _load_profile(current_user_id)
    dna = analyze_user_dna(profile)
    return {
        "user": {
            "id": current_user_id,
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "age": profile.get("age", 25),
            "favorite_genres": profile.get("favorite_genres", []),
            "favorite_actors": profile.get("favorite_actors", []),
            "favorite_actresses": profile.get("favorite_actresses", []),
            "favorite_directors": profile.get("favorite_directors", []),
            "favorite_writers": profile.get("favorite_writers", []),
            "bio": profile.get("bio", ""),
        },
        "dna": dna,
        "stats": {
            "total_watched": len(profile.get("watched", [])),
            "total_likes": len(profile.get("likes", [])),
            "total_searches": len(profile.get("searches", [])),
        },
    }


@router.get("/users/dna/{user_id}")
async def get_user_dna(user_id: str):
    profile = _load_profile(user_id)
    dna = analyze_user_dna(profile)
    return {"dna": dna, "user_id": user_id}


@router.get("/users/profile/{user_id}")
async def get_user_profile(user_id: str):
    profile = _load_profile(user_id)
    return {
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "age": profile.get("age", 25),
        "favorite_genres": profile.get("favorite_genres", []),
        "favorite_actors": profile.get("favorite_actors", []),
        "favorite_actresses": profile.get("favorite_actresses", []),
        "favorite_directors": profile.get("favorite_directors", []),
        "favorite_writers": profile.get("favorite_writers", []),
        "bio": profile.get("bio", ""),
    }


@router.put("/users/me")
async def update_profile(req: UpdateProfileRequest, current_user_id: str = Depends(get_current_user)):
    profile = _load_profile(current_user_id)
    if req.name is not None:
        profile["name"] = req.name
    if req.age is not None:
        profile["age"] = req.age
    if req.favorite_genres is not None:
        profile["favorite_genres"] = req.favorite_genres
    if req.favorite_actors is not None:
        profile["favorite_actors"] = req.favorite_actors
    if req.favorite_actresses is not None:
        profile["favorite_actresses"] = req.favorite_actresses
    if req.favorite_directors is not None:
        profile["favorite_directors"] = req.favorite_directors
    if req.favorite_writers is not None:
        profile["favorite_writers"] = req.favorite_writers
    if req.bio is not None:
        profile["bio"] = req.bio
    profile["updated_at"] = time.time()
    _save_profile(current_user_id, profile)
    dna = analyze_user_dna(profile)
    return {
        "user": {
            "id": current_user_id,
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "age": profile.get("age", 25),
            "favorite_genres": profile.get("favorite_genres", []),
            "favorite_actors": profile.get("favorite_actors", []),
            "favorite_actresses": profile.get("favorite_actresses", []),
            "favorite_directors": profile.get("favorite_directors", []),
            "favorite_writers": profile.get("favorite_writers", []),
            "bio": profile.get("bio", ""),
        },
        "dna": dna,
    }
