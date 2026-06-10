import yt_dlp
import asyncio
import time

CHANNELS = {
    "hum": {
        "name": "HUM TV",
        "handle": "@humtv",
        "url": "https://www.youtube.com/@humtv",
        "description": "Pakistan's leading entertainment channel featuring top-rated dramas.",
    },
    "geo": {
        "name": "Geo Entertainment",
        "handle": "@GeoEntertainment",
        "url": "https://www.youtube.com/@GeoEntertainment",
        "description": "Pakistan's largest television network for dramas and entertainment.",
    },
    "ary": {
        "name": "ARY Digital",
        "handle": "@ARYDigitalHD",
        "url": "https://www.youtube.com/@ARYDigitalHD",
        "description": "Popular Pakistani entertainment channel with hit dramas.",
    },
    "green": {
        "name": "Green TV",
        "handle": "@GreenTVEntertainment",
        "url": "https://www.youtube.com/@GreenTVEntertainment",
        "description": "Entertainment channel featuring quality Pakistani content.",
    },
}

FALLBACK_HANDLES = {
    "geo": ["@GeoEntertainment", "@GeoKahani"],
}

_cache = {}
CACHE_TTL = 600


def _cached(key, ttl=CACHE_TTL):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            now = time.time()
            cached = _cache.get(key)
            if cached and (now - cached["time"]) < ttl:
                return cached["data"]
            result = await func(*args, **kwargs)
            _cache[key] = {"data": result, "time": now}
            return result
        return wrapper
    return decorator


def _ydl_extract(url, extract_flat=True):
    opts = {
        "extract_flat": extract_flat,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 15,
        "retries": 1,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None


async def _run_ydl(url, extract_flat=True):
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, _ydl_extract, url, extract_flat),
        timeout=25,
    )


@_cached("channels")
async def get_channels():
    result = []
    for cid, ch in CHANNELS.items():
        avatar = None
        try:
            info = await _run_ydl(ch["url"], extract_flat=False)
            if info and info.get("thumbnails"):
                thumbs = sorted(info["thumbnails"], key=lambda t: t.get("width", 0) or 0, reverse=True)
                avatar = thumbs[0].get("url")
        except Exception:
            pass
        result.append({
            "id": cid,
            "name": ch["name"],
            "handle": ch["handle"],
            "description": ch["description"],
            "avatar": avatar,
        })
    return result


async def get_dramas(channel_id: str):
    ch = CHANNELS.get(channel_id)
    if not ch:
        return []
    cache_key = f"dramas:{channel_id}"

    @_cached(cache_key)
    async def _fetch():
        urls = [ch["url"] + "/playlists"]
        if channel_id in FALLBACK_HANDLES:
            for handle in FALLBACK_HANDLES[channel_id]:
                urls.append(f"https://www.youtube.com/{handle}/playlists")

        seen = set()
        result = []
        for url in urls:
            info = await _run_ydl(url)
            if not info:
                continue
            for e in info.get("entries", []):
                pid = e.get("id") or ""
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                thumb = None
                if e.get("thumbnails"):
                    thumbs = sorted(e["thumbnails"], key=lambda t: t.get("width", 0) or 0, reverse=True)
                    thumb = thumbs[0].get("url")
                result.append({
                    "id": pid,
                    "title": e.get("title", "Unknown"),
                    "thumbnail": thumb,
                    "channel": ch["name"],
                    "video_count": e.get("playlist_count") or e.get("n_entries") or 0,
                })
                if len(result) >= 30:
                    break
            if result:
                break
        return result

    return await _fetch()


async def get_episodes(playlist_id: str, channel_name: str = ""):
    cache_key = f"episodes:{playlist_id}"

    @_cached(cache_key)
    async def _fetch():
        info = await _run_ydl(f"https://www.youtube.com/playlist?list={playlist_id}")
        if not info:
            return None
        entries = info.get("entries", [])
        if not entries:
            return None

        title = info.get("title", "Unknown")
        thumb = None
        if info.get("thumbnails"):
            thumbs = sorted(info["thumbnails"], key=lambda t: t.get("width", 0) or 0, reverse=True)
            thumb = thumbs[0].get("url")

        episodes = []
        for i, e in enumerate(entries, 1):
            vid = e.get("id") or ""
            if not vid:
                continue
            ep_thumb = None
            if e.get("thumbnails"):
                et = sorted(e["thumbnails"], key=lambda t: t.get("width", 0) or 0, reverse=True)
                ep_thumb = et[0].get("url")
            episodes.append({
                "episode": i,
                "video_id": vid,
                "title": e.get("title", f"Episode {i}"),
                "thumbnail": ep_thumb,
                "duration": e.get("duration") or 0,
            })

        return {
            "playlist_id": playlist_id,
            "title": title,
            "thumbnail": thumb,
            "channel": channel_name or info.get("channel", ""),
            "episodes": episodes,
        }

    return await _fetch()
