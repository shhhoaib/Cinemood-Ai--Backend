from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mood, movies, chat, pakistani_dramas, recommendations, users

app = FastAPI(title="CineMood API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mood.router, prefix="/api/mood")
app.include_router(movies.router, prefix="/api/movies")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(pakistani_dramas.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "CineMood API"}
