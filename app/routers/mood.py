from fastapi import APIRouter, HTTPException
from app.models.schemas import MoodTextRequest, MoodImageRequest
from app.services.gemini import analyze_mood_text, analyze_mood_image
from app.services.tmdb import get_movies_for_mood

router = APIRouter()


@router.post("/text")
async def mood_from_text(req: MoodTextRequest):
    try:
        mood = await analyze_mood_text(req.text, req.events or "")
        movies = await get_movies_for_mood(mood["genres"])
        return {"mood": mood, "movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def mood_from_image(req: MoodImageRequest):
    try:
        mood = await analyze_mood_image(req.image_base64)
        movies = await get_movies_for_mood(mood["genres"])
        return {"mood": mood, "movies": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
