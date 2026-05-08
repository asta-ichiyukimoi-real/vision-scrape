import asyncio
import sys
from fastapi import FastAPI

from routers import webnovel, wikipedia, youtube, groq

app = FastAPI(
    title="Asta APIs",
    description="scraping test",
    version="1.0.0"
)

app.include_router(webnovel.router)
app.include_router(wikipedia.router)
app.include_router(youtube.router)
app.include_router(groq.router)


@app.get("/")
async def root():
    return {
        "message": "Asta APIs Hub for testing my scraping skill",
        "available_apis": {
            "wikipedia": "/wikipedia",
            "youtube": "/youtube",
            "groq_vision": "/groq",
            "webnovel": "/webnovel"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# uvicorn main:app --reload to host
