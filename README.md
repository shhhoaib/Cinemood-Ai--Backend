# CineMood AI - Mood-Driven Movie Recommender

A cinema-themed web application that analyzes your emotional state and recommends movies tailored to your mood. Features IMDb-style user ratings, Facebook-style comments, and multi-source review aggregation (IMDb, Rotten Tomatoes, Metacritic, TMDB).

## Tech Stack

- **Frontend:** React 18 + Vite 5 + Tailwind CSS 3 + Framer Motion + React Query (TanStack Query v5) + Zustand
- **Backend:** FastAPI (Python 3.12)
- **AI:** OpenRouter (Google Gemini 1.5 Pro)
- **Data:** TMDB API v3 + OMDB API (IMDb/RT/Metacritic ratings)
- **Deployment:** Vercel (Serverless Python + Static SPA)

## Live Demo

- **Frontend:** https://frontend-shhhoaibs-projects.vercel.app
- **Backend:** https://backend-nine-sigma-46.vercel.app/api/health

## Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.11+
- TMDB API key (free at themoviedb.org)
- OpenRouter API key (or Gemini API key)
- OMDB API key (free at omdbapi.com — optional, for IMDb/RT/Metacritic ratings)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server will proxy `/api` requests to `http://localhost:8000`.

### Environment Variables

**Backend** (`backend/.env`):
```
TMDB_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key
JWT_SECRET=your_secret
OMDB_API_KEY=your_key       # Optional — for IMDb/RT/Metacritic ratings
CINEMOOD_DATA_DIR=/tmp/data # Optional — override JSON data directory
```

**Frontend** (`frontend/.env`):
```
VITE_API_URL=http://localhost:8000/api
```

## Features

- **🎭 Mood Detection** — Describe your mood or upload a photo; AI analyzes and recommends matching movies
- **🎬 Multi-Source Ratings** — TMDB, IMDb, Rotten Tomatoes, Metacritic, and user ratings side by side
- **⭐ User Ratings** — Rate any movie/TV show 1-10, see aggregate scores with distribution histogram
- **💬 Comments** — Facebook-style threaded comments with replies, likes, and edit/delete
- **🧬 AI Emotional DNA** — Personalized user profiles with genre affinity and mood archetype matching
- **🎯 DNA Picks** — AI-generated recommendations based on your viewing history and preferences
- **🌍 14 Industry Sections** — Bollywood, Hollywood, Korean, Anime, Japanese, Indian, Tamil, Telugu, Punjabi, Pakistani, Bengali, Spanish, French, Turkish
- **🎭 Mood-Based Genres** — Emotion-to-genre mapping for targeted recommendations
- **📱 Fully Responsive** — Works on all devices with mobile navigation

## Project Structure

```
cinemood/
├── backend/
│   ├── api/
│   │   └── index.py              # Vercel serverless entry point
│   ├── app/
│   │   ├── main.py               # FastAPI entry point (local dev)
│   │   ├── routers/
│   │   │   ├── mood.py           # Mood analysis (text + image)
│   │   │   ├── movies.py         # Movie/TV search, detail, genres, industries
│   │   │   ├── chat.py           # AI chat assistant
│   │   │   ├── users.py          # Registration, login, profile, JWT auth
│   │   │   ├── reviews.py        # User comments/reviews (threaded, likes)
│   │   │   ├── ratings.py        # User ratings (1-10, aggregation, distribution)
│   │   │   ├── pakistani_dramas.py
│   │   │   └── recommendations.py
│   │   ├── services/
│   │   │   ├── tmdb.py           # TMDB API client + OMDB ratings
│   │   │   ├── gemini.py         # AI analysis via OpenRouter/Gemini
│   │   │   ├── user_dna.py       # User archetype & genre scoring
│   │   │   ├── user_profile.py   # Per-user profile JSON persistence
│   │   │   └── storage.py        # Shared data directory (Vercel /tmp fix)
│   │   ├── models/
│   │   └── utils/
│   ├── user_data/                # JSON data files (local dev)
│   ├── requirements.txt
│   ├── vercel.json
│   └── .vercelignore
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── backend.js        # Axios client with all API functions
│   │   ├── components/
│   │   │   ├── Navbar/           # Navigation with genre link
│   │   │   ├── Hero/             # Banner + horizontal scroll
│   │   │   ├── MovieCard/        # Movie card (poster, rating, genres)
│   │   │   ├── MovieGrid/
│   │   │   ├── MoodPicker/       # Mood selection UI
│   │   │   ├── MoodInput/
│   │   │   ├── Industry/         # Industry sidebar
│   │   │   ├── Reviews/          # StarRating + threaded comments
│   │   │   ├── ChatBot/
│   │   │   ├── UserDnaBadge/
│   │   │   └── UI/               # Loader, SkeletonGrid, InfiniteScroll
│   │   ├── pages/
│   │   │   ├── Home.jsx          # Hero, picks, industries, sections
│   │   │   ├── MovieDetail.jsx   # Detail, ratings, reviews, mood DNA
│   │   │   ├── MovieListing.jsx  # Discover with filters
│   │   │   ├── TVSeries.jsx
│   │   │   ├── GenrePage.jsx     # Genre movies with infinite scroll
│   │   │   ├── GenresPage.jsx    # All genres grid
│   │   │   ├── IndustryPage.jsx
│   │   │   ├── UpcomingPage.jsx
│   │   │   ├── TrendingPage.jsx
│   │   │   ├── TopRated.jsx
│   │   │   ├── SearchPage.jsx
│   │   │   ├── Recommend.jsx     # AI Therapist
│   │   │   ├── PersonPage.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Profile.jsx
│   │   │   ├── ForYou.jsx
│   │   │   └── PakistaniDramas.jsx
│   │   ├── store/               # Zustand stores (auth, mood)
│   │   ├── hooks/
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   └── vercel.json
└── README.md
```

## API Endpoints (43 routes)

### Movies
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/movies/trending` | Weekly trending movies |
| GET | `/api/movies/trending/tv` | Weekly trending TV |
| GET | `/api/movies/popular` | Popular movies (paginated) |
| GET | `/api/movies/popular/tv` | Popular TV (paginated) |
| GET | `/api/movies/top-rated` | Top rated movies |
| GET | `/api/movies/now-playing` | Now playing |
| GET | `/api/movies/upcoming` | Upcoming movies |
| GET | `/api/movies/discover` | Discover (filter, sort) |
| GET | `/api/movies/genre/{genre_id}` | By genre (paginated) |
| GET | `/api/movies/detail/{movie_id}` | Movie details (with user ratings) |
| GET | `/api/movies/mood-profile/{movie_id}` | Movie mood profile |
| GET | `/api/movies/tv/detail/{tv_id}` | TV details |
| GET | `/api/movies/tv/{tv_id}/seasons` | TV seasons |
| GET | `/api/movies/tv/{tv_id}/season/{num}` | TV episodes |
| GET | `/api/movies/search` | Search movies |
| GET | `/api/movies/search/multi` | Multi-search |
| GET | `/api/movies/genres` | Genre list |
| GET | `/api/movies/providers` | Watch providers by region |
| GET | `/api/movies/providers/trending` | Providers for trending |
| GET | `/api/movies/streaming/{provider_id}` | By streaming provider |
| GET | `/api/movies/industries` | Industry list (14 industries) |
| GET | `/api/movies/industry/{industry_id}` | By industry (Bollywood, Korean, etc.) |
| GET | `/api/movies/person/{person_id}` | Person credits |

### Mood
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/mood/text` | Analyze mood from text |
| POST | `/api/mood/image` | Analyze mood from image |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/message` | Chat with AI assistant |

### Pakistani Dramas
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dramas/channels` | Available channels |
| GET | `/api/dramas/channel/{id}` | Dramas by channel |
| GET | `/api/dramas/playlist/{id}` | Episodes in a drama |

### Recommendations
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/recommend/for-you` | Personalized recommendations |
| GET | `/api/recommend/dna-picks/{user_id}` | DNA-based picks |
| GET | `/api/recommend/profile` | User recommendation profile |
| POST | `/api/recommend/track/watch` | Track a watch |
| POST | `/api/recommend/track/like` | Track a like |
| POST | `/api/recommend/track/rating` | Track a rating |
| POST | `/api/recommend/track/search` | Track a search |

### Users
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/users/register` | Register account |
| POST | `/api/users/login` | Login |
| GET | `/api/users/me` | Get current user |
| PUT | `/api/users/me` | Update profile |
| GET | `/api/users/dna/{user_id}` | Get user DNA profile |

### Reviews & Comments
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/reviews` | Create review/comment |
| GET | `/api/reviews/{type}/{id}` | Get reviews (with reply threading) |
| PUT | `/api/reviews/{id}` | Edit own review |
| DELETE | `/api/reviews/{id}` | Delete own review + replies |
| POST | `/api/reviews/{id}/like` | Like a review |

### Ratings
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ratings` | Submit/update 1-10 rating |
| GET | `/api/ratings/{type}/{id}` | Get aggregate + user rating |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |

## Deployment

### Backend (Vercel)

```bash
cd backend
vercel --prod
```

Set environment variables (Production):
- `TMDB_API_KEY` — required
- `OPENROUTER_API_KEY` — required
- `JWT_SECRET` — required
- `OMDB_API_KEY` — optional, for IMDb/Rotten Tomatoes/Metacritic ratings

### Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

Set environment variable:
- `VITE_API_URL` — your deployed backend URL + `/api` (e.g. `https://your-app.vercel.app/api`)

> **Note:** Backend uses `/tmp` for JSON file storage on Vercel (read-only filesystem workaround). Data persists within a warm serverless instance but may reset on cold starts. For production persistence, add a database.
