MOOD_GENRE_MAP = {
    "happy": ["Comedy", "Adventure", "Animation"],
    "sad": ["Drama", "Romance", "Animation"],
    "anxious": ["Comedy", "Adventure", "Fantasy"],
    "excited": ["Action", "Science Fiction", "Adventure"],
    "angry": ["Action", "Thriller", "Drama"],
    "romantic": ["Romance", "Comedy", "Drama"],
    "nostalgic": ["Drama", "Animation", "Fantasy"],
    "bored": ["Action", "Science Fiction", "Thriller"],
    "stressed": ["Comedy", "Fantasy", "Animation"],
    "hopeful": ["Drama", "Adventure", "Fantasy"],
    "neutral": ["Drama", "Comedy", "Documentary"],
    "tired": ["Comedy", "Animation", "Fantasy"],
}


def get_genres_for_emotion(emotion: str) -> list:
    return MOOD_GENRE_MAP.get(emotion.lower(), ["Drama", "Comedy"])
