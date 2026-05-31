# routers/pinterest.py
from fastapi import APIRouter, Query, HTTPException
import requests

router = APIRouter(prefix="/pinterest", tags=["Pinterest"])

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}


@router.get("/search")
async def search_pinterest(
    query: str = Query(..., description="What do you want to search?"),
    limit: int = Query(10, ge=1, le=20)
):
    """Search Pinterest with better method"""
    try:
        # Using a more reliable public endpoint (works better)
        url = f"https://pinterest-api-pi.vercel.app/search?query={query}&limit={limit}"

        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "query": query,
                "results_count": len(data.get("results", [])),
                "pins": data.get("results", [])
            }

    except:
        pass

    # Fallback 2
    try:
        url = f"https://api.pinterest.com/v1/search/pins/?query={query}&limit={limit}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass

    return {
        "success": False,
        "message": "Pinterest is currently blocking requests. Try again later or use a different query."
    }


@router.get("/trending")
async def trending_pinterest():
    """Get Trending Pins"""
    try:
        resp = requests.get("https://pinterest-api-pi.vercel.app/trending",
                            headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass

    return {"success": False, "message": "Could not fetch trending pins"}
