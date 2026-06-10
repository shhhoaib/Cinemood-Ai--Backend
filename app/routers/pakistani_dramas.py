from fastapi import APIRouter, Query, HTTPException
from app.services.pakistani_dramas import get_channels, get_dramas, get_episodes

router = APIRouter()


@router.get("/dramas/channels")
async def list_channels():
    try:
        channels = await get_channels()
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dramas/channel/{channel_id}")
async def channel_dramas(channel_id: str):
    try:
        dramas = await get_dramas(channel_id)
        return {"dramas": dramas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dramas/playlist/{playlist_id}")
async def playlist_episodes(playlist_id: str, channel: str = Query("")):
    try:
        data = await get_episodes(playlist_id, channel)
        if not data:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
