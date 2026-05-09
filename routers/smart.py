# routers/smart.py
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from groq import Groq
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(prefix="/smart", tags=["Smart Assistant"])

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class SmartRequest(BaseModel):
    query: str
    max_sources: int = 5


@router.post("/")
async def smart_assistant(request: SmartRequest):
    """Smart Web Assistant - Searches + Reads + Summarizes with AI"""
    try:
        # Step 1: Do web search
        search_url = "https://html.duckduckgo.com/html/"
        resp = requests.post(search_url, data={"q": request.query},
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for result in soup.select(".result")[:request.max_sources]:
            title_tag = result.select_one(".result__title")
            link_tag = result.select_one(".result__url")
            snippet_tag = result.select_one(".result__snippet")

            if title_tag and link_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": link_tag.get("href"),
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                })

        # Step 2: Read content from top 2-3 pages
        context = ""
        for result in results[:3]:
            try:
                page = requests.get(result['url'], headers={
                                    "User-Agent": "Mozilla/5.0"}, timeout=8)
                page_soup = BeautifulSoup(page.text, "html.parser")

                # Remove scripts and styles
                for tag in page_soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()

                text = page_soup.get_text()
                text = ' '.join(text.split())[:2500]   # Limit text size
                context += f"\n\nSource: {result['title']}\n{text}\n"
            except:
                continue

        # Step 3: Use Groq AI to give final smart answer
        system_prompt = """
        You are Asta, created by Asta ichiyukimori a smart and friendly WhatsApp bot.
        Give clear, accurate, and engaging answers. Use the provided context.
        Always cite sources when possible. Be helpful and natural.
        """

        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {request.query}\n\nContext from web:\n{context}"}
            ],
            temperature=0.7,
            max_tokens=1200
        )

        return {
            "success": True,
            "query": request.query,
            "answer": final_response.choices[0].message.content,
            "sources": results[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Smart assistant failed")


# Quick GET version for testing
@router.get("/")
async def smart_assistant_get(query: str = Query(...)):
    req = SmartRequest(query=query)
    return await smart_assistant(req)
