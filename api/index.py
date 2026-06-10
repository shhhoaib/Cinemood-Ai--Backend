import sys
from pathlib import Path
root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

application = FastAPI(title="CineMood API", version="1.0.0")

application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import mood, movies, chat, pakistani_dramas, recommendations, users, reviews, ratings
application.include_router(mood.router, prefix="/api/mood")
application.include_router(movies.router, prefix="/api/movies")
application.include_router(chat.router, prefix="/api/chat")
application.include_router(pakistani_dramas.router, prefix="/api")
application.include_router(recommendations.router, prefix="/api")
application.include_router(users.router, prefix="/api")
application.include_router(reviews.router, prefix="/api")
application.include_router(ratings.router, prefix="/api")

@application.get("/api/health")
async def health():
    return {"status": "ok"}

app = application
