# routers/imdb.py
from fastapi import APIRouter, Query, HTTPException
import requests

router = APIRouter(prefix="/imdb", tags=["IMDb"])


@router.get("/search")
async def search_movie(q: str = Query(...)):
    try:
        url = f"https://search.imdb.com/search?q={q}"
        # Better to use OMDB API (free) or just scrape lightly
        # For now using a public endpoint
        resp = requests.get(
            f"https://www.omdbapi.com/?apikey=yourkey&t={q}", timeout=10)
        data = resp.json()

        return data
    except:
        raise HTTPException(500, "Failed to fetch movie data")
