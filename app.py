import os
import json
import logging
from typing import Dict

import uvicorn
from fastapi import FastAPI
from src.router.zalo.router import zalo_router
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Webhook Chatbot Enso")

app.include_router(zalo_router, prefix="/zalo", tags=["webhook"])


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="static"), name="static")
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
