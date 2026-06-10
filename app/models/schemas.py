from pydantic import BaseModel
from typing import Optional, List


class MoodTextRequest(BaseModel):
    text: str
    events: Optional[str] = None


class MoodImageRequest(BaseModel):
    image_base64: str


class MoodResponse(BaseModel):
    emotion: str
    intensity: float
    genres: List[str]
    summary: str
    movie_prompt: str


class MovieRecommendResponse(BaseModel):
    mood: MoodResponse
    movies: List[dict]


class ChatRequest(BaseModel):
    messages: List[dict]
    mood: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    movies: Optional[List[dict]] = None
