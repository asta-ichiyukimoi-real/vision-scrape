# main.py
from fastapi import FastAPI
from routers import wikipedia, youtube, groq     # ← Add groq

app = FastAPI(
    title="MyWeb - All My APIs",
    description="Unified API Hub",
    version="1.0.0"
)

# Include all routers
app.include_router(wikipedia.router)
app.include_router(youtube.router)
app.include_router(groq.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to MyWeb API Hub",
        "available_apis": {
            "wikipedia": "/wikipedia",
            "youtube": "/youtube",
            "groq_vision": "/groq"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
