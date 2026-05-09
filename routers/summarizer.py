# routers/summarizer.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
import requests
from bs4 import BeautifulSoup
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/summarize", tags=["Summarizer"])

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class SummarizeRequest(BaseModel):
    url: HttpUrl
    length: str = Query("medium", description="short, medium, long")


@router.post("/")
async def summarize_url(request: SummarizeRequest):
    """Summarize any article or webpage"""
    try:
        # Fetch webpage
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(str(request.url), headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Clean text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()[:8000]  # Limit size

        # Use Groq to summarize
        prompt = f"""Summarize the following article in {request.length} length.
        Focus on the main points and key takeaways.

        Article: {text}"""

        response = client.chat.completions.create(
            # or use "llama-3.3-70b-versatile" if available
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )

        return {
            "success": True,
            "url": str(request.url),
            "summary": response.choices[0].message.content,
            "length": request.length
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
