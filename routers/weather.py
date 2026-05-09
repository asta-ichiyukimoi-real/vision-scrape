# routers/weather.py
from fastapi import APIRouter, Query, HTTPException
import requests

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/")
async def get_weather(city: str = Query(..., description="City name")):
    """Get current weather"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        current = data['current_condition'][0]

        return {
            "success": True,
            "city": city,
            "temperature": current['temp_C'],
            "condition": current['lang'][0]['value'],
            "humidity": current['humidity'],
            "wind_speed": current['windspeedKmph'],
            "feels_like": current['FeelsLikeC']
        }
    except:
        raise HTTPException(500, "Could not fetch weather")
