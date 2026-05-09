# routers/search.py
from fastapi import APIRouter, Query, HTTPException
import requests
from bs4 import BeautifulSoup
import re

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
async def web_search(q: str = Query(..., description="Search query"), limit: int = 8):
    """Real-time web search using DuckDuckGo"""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        data = {"q": q}

        resp = requests.post(url, headers=headers, data=data, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for result in soup.select(".result")[:limit]:
            title = result.select_one(".result__title")
            snippet = result.select_one(".result__snippet")
            link = result.select_one(".result__url")

            if title and link:
                results.append({
                    "title": title.get_text(strip=True),
                    "snippet": snippet.get_text(strip=True) if snippet else "",
                    "url": link.get("href", "")
                })

        return {
            "success": True,
            "query": q,
            "results_count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Search failed")
