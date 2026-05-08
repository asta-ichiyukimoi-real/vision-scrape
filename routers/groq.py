# routers/groq.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(prefix="/groq", tags=["Groq AI"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise Exception("❌ GROQ_API_KEY is not set!")

client = Groq(api_key=GROQ_API_KEY)


# ====================== POST Version (Recommended) ======================
class VisionRequest(BaseModel):
    image_url: HttpUrl
    prompt: str = "Describe this image in detail and extract all text."
    temperature: float = 0.5


@router.post("/vision")
async def describe_image(request: VisionRequest):
    """Describe image using POST (better for long prompts)"""
    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": request.prompt},
                    {"type": "image_url", "image_url": {
                        "url": str(request.image_url)}}
                ]
            }],
            temperature=request.temperature
        )

        return {
            "success": True,
            "description": response.choices[0].message.content,
            "image_url": str(request.image_url)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ====================== GET Version (For quick testing) ======================
@router.get("/vision")
async def describe_image_get(
    image_url: HttpUrl = Query(..., description="Public image URL"),
    prompt: str = Query("Describe this image in detail and extract all text.")
):
    """Describe image using GET request"""
    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": str(image_url)}}
                ]
            }],
            temperature=0.5
        )

        return {
            "success": True,
            "description": response.choices[0].message.content,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
