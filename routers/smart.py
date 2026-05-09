# routers/smart.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os
import re
from typing import List, Dict
from collections import defaultdict

load_dotenv()

router = APIRouter(prefix="/smart", tags=["Smart Assistant"])

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")

if not CEREBRAS_API_KEY:
    raise Exception("CEREBRAS_API_KEY is not set!")

client = Cerebras(api_key=CEREBRAS_API_KEY)

# Store chat history
smart_history: Dict[str, List[dict]] = defaultdict(list)

ASTA_SYSTEM_PROMPT = """
You are Asta, created by Asta Ichiyukimori, a friendly WhatsApp bot.
Reply like a normal chat friend: short, natural, helpful, and casual.
For greetings, small talk, thanks, jokes, or simple chat, do not explain or over-answer.
When fresh web context is provided, use it only if it actually helps answer the user.
Do not explain obvious words or give dictionary-style definitions unless asked.
Do not say you searched or list sources in the chat reply unless asked.
"""


class SmartRequest(BaseModel):
    query: str
    session_id: str = "default"
    max_sources: int = 5


def should_search_web(query: str) -> bool:
    """Use web search only when the user likely needs fresh/factual info."""
    normalized = query.strip().lower()

    if len(normalized) <= 3:
        return False

    casual_patterns = [
        r"^(hi|hey|hello|yo|sup|wyd|gm|gn|good morning|good afternoon|good evening)[!. ]*$",
        r"^(thanks|thank you|ty|ok|okay|cool|nice|lol|haha|bye)[!. ]*$",
        r"^(how are you|what'?s up|whats up|who are you)[?.! ]*$",
    ]
    if any(re.match(pattern, normalized) for pattern in casual_patterns):
        return False

    current_keywords = [
        "latest", "today", "now", "current", "recent", "news", "update",
        "price", "weather", "score", "schedule", "release", "version",
        "who won", "when is", "where is", "search", "look up", "find"
    ]
    if any(keyword in normalized for keyword in current_keywords):
        return True

    question_starters = (
        "what is", "what are", "who is", "who are", "when did", "when was",
        "where is", "where are", "why is", "why are", "how to", "how do",
        "how does", "tell me about", "explain"
    )
    return normalized.startswith(question_starters)


@router.post("/")
async def smart_assistant(request: SmartRequest):
    """Smart Web Assistant with Memory + Asta Personality"""
    try:
        history = smart_history[request.session_id]

        # Add system prompt only once
        if not history:
            history.append({"role": "system", "content": ASTA_SYSTEM_PROMPT})

        results = []
        context = ""

        if should_search_web(request.query):
            # Step 1: Web Search
            search_resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": request.query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )

            soup = BeautifulSoup(search_resp.text, "html.parser")

            for result in soup.select(".result")[:request.max_sources]:
                title = result.select_one(".result__title")
                link = result.select_one(".result__url")
                snippet = result.select_one(".result__snippet")

                if title and link:
                    results.append({
                        "title": title.get_text(strip=True),
                        "url": link.get("href"),
                        "snippet": snippet.get_text(strip=True) if snippet else ""
                    })

            # Step 2: Read content from top pages
            for result in results[:3]:
                try:
                    page = requests.get(result["url"], headers={
                                        "User-Agent": "Mozilla/5.0"}, timeout=10)
                    page_soup = BeautifulSoup(page.text, "html.parser")

                    for tag in page_soup(["script", "style", "nav", "header", "footer"]):
                        tag.decompose()

                    text = page_soup.get_text()
                    text = " ".join(text.split())[:2800]
                    context += f"\n\nSource: {result['title']}\n{text}\n"
                except:
                    continue

        # Step 3: Final Answer with Cerebras + Memory
        if context:
            user_message = (
                f"User message: {request.query}\n\n"
                f"Fresh web context, only use if relevant:\n{context}"
            )
        else:
            user_message = request.query

        history.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=history,
            temperature=0.8,
            max_tokens=1200
        )

        ai_reply = response.choices[0].message.content

        history.append({"role": "assistant", "content": ai_reply})

        # Limit history size
        if len(history) > 15:
            history[:] = [history[0]] + history[-14:]

        return {
            "success": True,
            "session_id": request.session_id,
            "response": ai_reply,
            "sources": results[:5]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Smart Assistant Error: {str(e)}")


# GET version for easy testing
@router.get("/")
async def smart_assistant_get(
    query: str = Query(..., description="Your question"),
    session_id: str = Query("default")
):
    req = SmartRequest(query=query, session_id=session_id)
    return await smart_assistant(req)


# Clear history
@router.delete("/history")
async def clear_smart_history(session_id: str = "default"):
    if session_id in smart_history:
        smart_history[session_id].clear()
        return {"success": True, "message": f"Smart history cleared for {session_id}"}
    return {"success": False, "message": "No history found"}
