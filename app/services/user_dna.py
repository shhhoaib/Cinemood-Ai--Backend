import json

DNA_ARCHETYPES = [
    {
        "id": "action_junkie",
        "name": "The Action Junkie",
        "emoji": "\U0001f525",
        "tagline": "You live for explosions, car chases, and adrenaline-pumping fight scenes.",
        "description": "High-octane thrills are your thing. From superhero blockbusters to martial arts masterpieces, you crave intensity and spectacle.",
        "keywords": ["action", "adventure", "thriller", "war", "martial arts", "superhero"],
        "genres": [28, 12, 53, 10752, 10759],
        "age_range": [13, 40],
    },
    {
        "id": "drama_connoisseur",
        "name": "The Drama Connoisseur",
        "emoji": "\U0001f3ad",
        "tagline": "You appreciate powerful storytelling, complex characters, and emotional depth.",
        "description": "Award-winning dramas, character-driven narratives, and films that make you think — that's your sweet spot.",
        "keywords": ["drama", "emotional", "character-driven", "slow burn", "literary"],
        "genres": [18, 10749, 36],
        "age_range": [18, 99],
    },
    {
        "id": "horror_aficionado",
        "name": "The Horror Aficionado",
        "emoji": "\U0001f47b",
        "tagline": "You sleep with the lights off because real horrors are on the screen.",
        "description": "Psychological thrillers, supernatural scares, slasher flicks — if it makes your heart race, you're all in.",
        "keywords": ["horror", "thriller", "suspense", "supernatural", "psychological"],
        "genres": [27, 53, 9648],
        "age_range": [16, 50],
    },
    {
        "id": "comedy_fanatic",
        "name": "The Comedy Fanatic",
        "emoji": "\U0001f604",
        "tagline": "Laughter is your medicine and comedy is your therapy.",
        "description": "From slapstick to satire, stand-up specials to rom-coms — you're always looking for the next big laugh.",
        "keywords": ["comedy", "funny", "humor", "satire", "feel-good"],
        "genres": [35, 10749, 10402],
        "age_range": [10, 60],
    },
    {
        "id": "scifi_nerd",
        "name": "The Sci-Fi Nerd",
        "emoji": "\U0001f4a1",
        "tagline": "You dream of distant galaxies, alternate realities, and futuristic technology.",
        "description": "Space operas, time travel paradoxes, dystopian futures — you love stories that push the boundaries of imagination.",
        "keywords": ["sci-fi", "fantasy", "futuristic", "space", "technology", "time travel"],
        "genres": [878, 14, 10765, 12],
        "age_range": [10, 60],
    },
    {
        "id": "cinephile",
        "name": "The Complete Cinephile",
        "emoji": "\U0001f3ac",
        "tagline": "You don't just watch movies — you experience them.",
        "description": "Your taste knows no bounds. From indie darlings to blockbuster epics, you appreciate the art of cinema in all its forms.",
        "keywords": ["everything", "cinema", "art", "global", "eclectic"],
        "genres": [],
        "age_range": [1, 99],
    },
    {
        "id": "romantic",
        "name": "The Hopeless Romantic",
        "emoji": "\U0001f497",
        "tagline": "You believe in love stories and happy endings.",
        "description": "Romantic comedies, period dramas, tearjerkers — if it's about love, you're watching it with popcorn and tissues ready.",
        "keywords": ["romance", "love", "romantic comedy", "relationship", "emotional"],
        "genres": [10749, 35, 18],
        "age_range": [13, 70],
    },
    {
        "id": "mystery_noir",
        "name": "The Mystery Solver",
        "emoji": "\U0001f50d",
        "tagline": "You love puzzles, plot twists, and keeping one step ahead of the detective.",
        "description": "Crime procedurals, noir thrillers, whodunits — you're always trying to crack the case before the final act.",
        "keywords": ["mystery", "crime", "noir", "detective", "suspense", "plot twist"],
        "genres": [9648, 80, 53],
        "age_range": [16, 80],
    },
    {
        "id": "tv_binger",
        "name": "The Binge Master",
        "emoji": "\U0001f4fa",
        "tagline": "Movies are great, but you live for multi-season epics.",
        "description": "You prefer the deep character development and sprawling narratives that only TV series can deliver.",
        "keywords": ["tv series", "binge", "long-form", "series", "episodic"],
        "genres": [],
        "age_range": [13, 70],
    },
    {
        "id": "animation_lover",
        "name": "The Animation Enthusiast",
        "emoji": "\u2728",
        "tagline": "You know animation isn't just for kids — it's an art form.",
        "description": "From Studio Ghibli to anime epics, from Pixar to adult animation — you appreciate the craft of animated storytelling.",
        "keywords": ["animation", "anime", "cartoon", "studio ghibli", "pixar"],
        "genres": [16, 14],
        "age_range": [1, 70],
    },
    {
        "id": "documentary_buff",
        "name": "The Truth Seeker",
        "emoji": "\U0001f4f9",
        "tagline": "Reality is stranger than fiction, and you love every minute of it.",
        "description": "Documentaries, docuseries, biopics — you crave real stories about real people and real events.",
        "keywords": ["documentary", "true story", "biopic", "history", "educational"],
        "genres": [99, 36],
        "age_range": [16, 80],
    },
    {
        "id": "bollywood_bhakt",
        "name": "The Bollywood Devotee",
        "emoji": "\U0001faa9",
        "tagline": "You believe every movie needs a song, a dance, and a dramatic family reunion.",
        "description": "Masala entertainers, romantic sagas, and larger-than-life heroes — Bollywood is your heartbeat.",
        "keywords": ["bollywood", "indian cinema", "masala", "song and dance", "drama"],
        "genres": [],
        "age_range": [5, 99],
    },
    {
        "id": "family_entertainer",
        "name": "The Family Entertainer",
        "emoji": "\U0001f46a",
        "tagline": "Movie night is family night — and everyone has to agree on the pick.",
        "description": "Wholesome content the whole family can enjoy. Animated adventures, family comedies, and heartwarming tales.",
        "keywords": ["family", "kids", "wholesome", "fun for all ages", "animated"],
        "genres": [10751, 16, 35, 12],
        "age_range": [1, 60],
    },
    {
        "id": "indie_hipster",
        "name": "The Indie Auteur",
        "emoji": "\U0001f3b5",
        "tagline": "You liked it before it was mainstream.",
        "description": "A24 darlings, festival circuit gems, foreign films — you seek out the unique, the artistic, and the unconventional.",
        "keywords": ["indie", "arthouse", "foreign", "a24", "festival", "experimental"],
        "genres": [18, 10749, 9648],
        "age_range": [18, 70],
    },
    {
        "id": "nostalgia_seeker",
        "name": "The Nostalgia Seeker",
        "emoji": "\U0001f3b0",
        "tagline": "They don't make 'em like they used to — and you're okay with that.",
        "description": "Classic films, retro series, vintage cinema — you love revisiting the golden eras of entertainment.",
        "keywords": ["classic", "retro", "vintage", "old school", "80s", "90s"],
        "genres": [36, 18, 35],
        "age_range": [30, 90],
    },
]


TMDB_GENRE_NAMES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10765: "Sci-Fi & Fantasy",
}


GENRE_OWNER = {
    28: "action_junkie", 12: "action_junkie", 10752: "action_junkie", 10759: "action_junkie",
    35: "comedy_fanatic", 10402: "comedy_fanatic",
    18: "drama_connoisseur",
    36: "documentary_buff",
    99: "documentary_buff",
    10751: "family_entertainer",
    27: "horror_aficionado", 53: "horror_aficionado",
    9648: "mystery_noir", 80: "mystery_noir",
    10749: "romantic",
    878: "scifi_nerd", 14: "scifi_nerd", 10765: "scifi_nerd",
    37: "nostalgia_seeker",
    16: "animation_lover",
}

DIRECTOR_AFFINITY = {
    "scifi_nerd": ["christopher nolan", "denis villeneuve", "ridley scott", "james cameron", "steven spielberg"],
    "horror_aficionado": ["jordan peele", "ari aster", "john carpenter", "mike flanagan", "james wan"],
    "indie_hipster": ["greta gerwig", "paul thomas anderson", "yorgos lanthimos", "wes anderson", "safdie brothers"],
    "action_junkie": ["michael bay", "zack snyder", "chad stahelski", "james cameron", "james gunn"],
    "comedy_fanatic": ["judd apatow", "taika waititi", "edgar wright", "wes anderson"],
    "animation_lover": ["hayao miyazaki", "makoto shinkai", "brad bird", "pete docter"],
    "drama_connoisseur": ["martin scorsese", "steven spielberg", "denis villeneuve", "christopher nolan", "paul thomas anderson"],
    "nostalgia_seeker": ["steven spielberg", "stanley kubrick", "alfred hitchcock", "francis ford coppola"],
    "mystery_noir": ["alfred hitchcock", "david fincher", "denis villeneuve", "bong joon-ho"],
}

ACTOR_AFFINITY = {
    "nostalgia_seeker": ["marlon brando", "james dean", "audrey hepburn", "cary grant", "elizabeth taylor"],
    "animation_lover": ["hayao miyazaki", "makoto shinkai"],
    "action_junkie": ["dwayne johnson", "jason statham", "keanu reeves", "tom hardy", "chris hemsworth", "scarlett johansson"],
    "drama_connoisseur": ["leonardo dicaprio", "meryl streep", "daniel day-lewis", "cate blanchett", "denzel washington"],
}

INDIAN_ACTORS = [
    "shah rukh khan", "salman khan", "aamir khan", "ranbir kapoor",
    "deepika padukone", "alia bhatt", "hrithik roshan", "akshay kumar",
    "priyanka chopra", "kareena kapoor", "shahid kapoor",
]


def _get_archetype(archetype_id: str) -> dict:
    return next(a for a in DNA_ARCHETYPES if a["id"] == archetype_id)


def analyze_user_dna(user_data: dict) -> dict:
    watched = user_data.get("watched", [])
    likes = user_data.get("likes", [])

    fav_genres = user_data.get("favorite_genres", [])
    fav_actors = user_data.get("favorite_actors", [])
    fav_directors = user_data.get("favorite_directors", [])
    age = user_data.get("age", 25)
    bio = user_data.get("bio", "") or ""

    fav_genre_ids = []
    for g in fav_genres:
        if isinstance(g, int):
            fav_genre_ids.append(g)
        elif isinstance(g, str) and g.isdigit():
            fav_genre_ids.append(int(g))

    genre_count = {}
    for w in watched:
        for g in w.get("genres", []):
            genre_count[g] = genre_count.get(g, 0) + 1
    for w in watched:
        if w.get("completed"):
            for g in w.get("genres", []):
                genre_count[g] = genre_count.get(g, 0) + 0.5
    for g in fav_genre_ids:
        genre_count[g] = genre_count.get(g, 0) + 3

    top_genres = sorted(genre_count.items(), key=lambda x: -x[1])[:3]
    top_genre_ids = [g[0] for g in top_genres]

    bio_lower = bio.lower()

    scores = {}
    for archetype in DNA_ARCHETYPES:
        aid = archetype["id"]
        a_genres = archetype.get("genres", [])
        a_keywords = archetype.get("keywords", [])
        score = 0.0

        for gid in top_genre_ids:
            if gid in a_genres:
                score += 2.0

        for gid in fav_genre_ids:
            if gid in a_genres:
                score += 3.0

        ar_min, ar_max = archetype.get("age_range", [0, 99])
        if ar_min <= age <= ar_max:
            score += 1.0

        if len(watched) > 30:
            tv_count = sum(1 for w in watched if w.get("media_type") == "tv")
            if aid == "tv_binger" and tv_count > len(watched) * 0.5:
                score += 5.0
            elif aid != "tv_binger" and tv_count > len(watched) * 0.5:
                score -= 2.0

        if fav_directors and aid == "cinephile":
            score += 2.0

        if aid == "bollywood_bhakt":
            for a_name in fav_actors:
                if any(indian in a_name.lower() for indian in INDIAN_ACTORS):
                    score += 5.0
                    break

        for kw in a_keywords:
            if kw in bio_lower:
                score += 2.0

        for gid in fav_genre_ids:
            if gid in a_genres and GENRE_OWNER.get(gid) == aid:
                score += 1.5

        for a_name in fav_actors:
            affinity_list = ACTOR_AFFINITY.get(aid, [])
            if any(name in a_name.lower() for name in affinity_list):
                score += 3.0
                break

        for d_name in fav_directors:
            affinity_list = DIRECTOR_AFFINITY.get(aid, [])
            if d_name.lower() in affinity_list:
                score += 3.0
                break

        scores[aid] = score

    if not scores or max(scores.values()) == 0:
        scores["cinephile"] = 10.0

    primary_id = max(scores, key=lambda k: (
        scores[k],
        sum(1 for kw in _get_archetype(k).get("keywords", []) if kw in bio_lower),
    ))
    primary = _get_archetype(primary_id)
    primary_score = scores[primary_id]

    secondary_archetypes = sorted(
        [(sid, s) for sid, s in scores.items() if sid != primary_id and s > 0],
        key=lambda x: -x[1],
    )[:2]
    secondaries = []
    for sid, sc in secondary_archetypes:
        a = _get_archetype(sid)
        secondaries.append({
            "id": a["id"],
            "name": a["name"],
            "emoji": a["emoji"],
            "score": round(sc, 1),
        })

    genre_labels = [TMDB_GENRE_NAMES.get(g, "Unknown") for g in top_genre_ids]

    return {
        "primary": {
            "id": primary["id"],
            "name": primary["name"],
            "emoji": primary["emoji"],
            "tagline": primary["tagline"],
            "description": primary["description"],
            "score": round(primary_score, 1),
        },
        "secondary": secondaries,
        "top_genres": genre_labels,
        "total_watched": len(watched),
        "total_likes": len(likes),
        "actor_count": len(fav_actors),
        "director_count": len(fav_directors),
    }
