# main.py
from fastapi import APIRouter, FastAPI, Query
import requests
from bs4 import BeautifulSoup
import re

router = APIRouter(
    prefix="/wikipedia",
    tags=["Wikipedia"]
)

HEADERS = {
    # ← Use your real User-Agent
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def clean_snippet(text: str) -> str:
    """Clean HTML tags and extra spaces from snippets"""
    if not text:
        return ""
    # Remove HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()
    # Remove extra spaces and citations
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


@router.get("/search")
async def search_wikipedia(q: str = Query(None), limit: int = Query(5)):
    """Clean & Beautiful Search"""
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": q,
        "srlimit": limit
    }

    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    data = resp.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        results.append({
            "title": item["title"],
            "snippet": clean_snippet(item.get("snippet", "")),
            "url": f"https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
            "pageid": item.get("pageid")
        })

    return {
        "success": True,
        "query": q,
        "results_count": len(results),
        "author": 'Asta ichiyukimori',
        "results": results
    }


@router.get("/page")
async def get_page(title: str):
    """Get detailed page info"""
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    resp = requests.get(summary_url, headers=HEADERS, timeout=10)

    if resp.status_code != 200:
        return {"success": False, "error": "Page not found"}

    data = resp.json()

    return {
        "success": True,
        "title": data.get("title"),
        "summary": data.get("extract"),
        "thumbnail": data.get("thumbnail", {}).get("source"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page")
    }
