# routers/ai.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
from typing import Optional, List, Dict
from collections import defaultdict

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI Chat"])

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Store chat history in memory
chat_history: Dict[str, List[dict]] = defaultdict(list)

DEFAULT_SYSTEM_PROMPT = """
You are Asta,created by Asta ichiyukimori, a fun, friendly, and slightly playful WhatsApp bot.
You speak casually like a real friend on WhatsApp. Use emojis, short sentences, and slang.
Be helpful, witty, and sometimes teasing. 
Keep responses natural and conversational. Never sound too formal or robotic.
"""


class AIRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.85
    max_tokens: Optional[int] = 1024
    system_prompt: Optional[str] = None


@router.post("/chat")
async def ai_chat(request: AIRequest):
    """Main endpoint - Chat with Asta Ichiyukimori (with memory)"""
    try:
        history = chat_history[request.session_id]

        # Add system prompt only at the beginning
        if not history:
            system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
            history.append({"role": "system", "content": system_prompt})

        # Add user message
        history.append({"role": "user", "content": request.message})

        # Call Groq
        response = client.chat.completions.create(
            model=request.model,
            messages=history,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        ai_reply = response.choices[0].message.content

        # Save assistant reply to history
        history.append({"role": "assistant", "content": ai_reply})

        # Keep only last 20 messages + system prompt to save tokens
        if len(history) > 21:
            history[:] = [history[0]] + history[-20:]

        return {
            "success": True,
            "session_id": request.session_id,
            "response": ai_reply,
            "character": "Asta"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


@router.get("/chat")
async def ai_chat_get(
    message: str = Query(..., description="Your message to Asta"),
    session_id: str = Query("default", description="Chat session ID")
):
    """Quick testing with GET method"""
    try:
        request = AIRequest(message=message, session_id=session_id)
        return await ai_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Clear history for a specific session
@router.delete("/chat/history")
async def clear_history(session_id: str = "default"):
    if session_id in chat_history:
        chat_history[session_id].clear()
        return {"success": True, "message": f"History cleared for session: {session_id}"}
    return {"success": False, "message": "No history found for this session"}
