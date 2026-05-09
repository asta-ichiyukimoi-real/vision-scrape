from fastapi import APIRouter, Query, HTTPException
import yt_dlp
import asyncio
from typing import Optional

router = APIRouter(
    prefix="/youtube",
    tags=["YouTube"]
)


async def extract_info(url: str, opts: dict = None):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        **(opts or {})
    }
    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            return info
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error extracting info: {str(e)}"
        )


@router.get("/video")
async def get_video_info(url: str = Query(..., description="YouTube video or shorts URL")):
    """Get basic video information"""
    info = await extract_info(url)
    return {
        "title": info.get("title"),
        "id": info.get("id"),
        "channel": info.get("channel"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "upload_date": info.get("upload_date"),
    }


@router.get("/search")
async def search_youtube(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(10, ge=1, le=50)
):
    """Search YouTube videos"""
    search_url = f"ytsearch{max_results}:{q}"
    info = await extract_info(search_url, {"extract_flat": True})

    results = []
    for entry in info.get("entries", []):
        results.append({
            "id": entry.get("id"),
            "title": entry.get("title"),
            "channel": entry.get("channel"),
            "duration": entry.get("duration"),
            "view_count": entry.get("view_count"),
            "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
        })

    return {"query": q, "results": results}


@router.get("/playlist")
async def get_playlist(url: str = Query(..., description="YouTube playlist URL")):
    """Get playlist information"""
    info = await extract_info(url, {"extract_flat": True})
    return {
        "title": info.get("title"),
        "id": info.get("id"),
        "channel": info.get("channel"),
        "video_count": len(info.get("entries", [])),
        "videos": info.get("entries", [])
    }


@router.get("/transcript")
async def get_transcript(video_id: str):
    """Get video transcript"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    info = await extract_info(url, {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True
    })

    return {
        "manual_subtitles": info.get("subtitles"),
        "auto_captions": info.get("automatic_captions")
    }


@router.get("/download")
async def get_download_link(
    url: str = Query(..., description="YouTube video URL"),
    quality: str = Query(
        "best", description="best, 1080p, 720p, 480p, audio, mp3")
):
    format_map = {
        "best": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best",
        "audio": "bestaudio/best",
        "mp3": "bestaudio/best",
    }

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': format_map.get(quality, "bestvideo+bestaudio/best"),
        'merge_output_format': 'mp4',
        'no_warnings': True,
    }

    if quality == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    try:
        info = await extract_info(url, ydl_opts)

        # Extract direct URL
        direct_url = None
        if info.get('requested_formats'):
            direct_url = info['requested_formats'][-1].get('url')
        elif info.get('url'):
            direct_url = info.get('url')

        return {
            "title": info.get("title"),
            "id": info.get("id"),
            "direct_download_url": direct_url,
            "requested_quality": quality,
            "message": "Direct link may expire soon."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Download error: {str(e)}")
