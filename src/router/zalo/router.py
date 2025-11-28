# main.py
import os
import json
import asyncio
import logging
from typing import Dict, Any
import httpx
from fastapi import FastAPI, APIRouter, Request, Path, HTTPException

from dotenv import load_dotenv
from src.router.zalo._schema import ZaloChatRequest
from src.utils import call_dify_workflow, send_zalo_message, WORKFLOWS

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zalo_webhook")

# -----------------------------
_sessions: Dict[str, Dict[str, Any]] = {}
_sessions_lock = asyncio.Lock()

# -----------------------------
# FastAPI & Router
# -----------------------------
app = FastAPI()
zalo_router = APIRouter()


# -----------------------------
# Process user message
# -----------------------------
async def process_message(bot_id: str, user_id: str, user_message: str) -> None:
    logger.info(
        f"Processing message for bot_id={bot_id}, user_id={user_id}, message={user_message}"
    )

    session_key = f"{bot_id}:{user_id}"
    async with _sessions_lock:
        session = _sessions.get(session_key) or {"context": {}}
        _sessions[session_key] = session

    try:
        bot_reply = await call_dify_workflow(bot_id, user_message, session=session)
        logger.info(
            f"Dify replied: {bot_reply[:100]}..."
            if len(bot_reply) > 100
            else f"Dify replied: {bot_reply}"
        )

        async with _sessions_lock:
            session = _sessions.get(session_key, {"context": {}})
            session["context"]["last_bot_msg"] = bot_reply
            _sessions[session_key] = session

        await send_zalo_message(user_id, bot_reply)
        logger.info(f"Successfully sent message to Zalo user_id={user_id}")

    except Exception as e:
        logger.error(f"Error processing message for user_id={user_id}: {e}")


# -----------------------------
# Zalo webhook endpoint
# -----------------------------
@zalo_router.post("/webhook/{bot_id}")
async def zalo_webhook(
    request: Request,
    bot_id: str = Path(..., description="ID của bot để phân biệt workflow Dify"),
) -> Dict[str, Any]:

    if bot_id not in WORKFLOWS:
        return {"status": "ignored", "reason": f"unknown bot_id {bot_id}"}

    try:
        raw = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = raw.get("event_name")
    logger.info(f"Webhook received: bot_id={bot_id}, event_name={event_name}")

    if event_name == "user_send_text":
        try:
            chat_req = ZaloChatRequest(
                sender=raw.get("sender", {}).get("id"),
                message=raw.get("message", {}).get("text") or "",
                metadata=raw.get("metadata", {}) or {},
            )
        except Exception as e:
            logger.warning(f"Invalid payload: {e}, raw={raw}")
            return {"status": "ignored", "reason": "invalid payload"}

        user_id = chat_req.sender
        user_message = chat_req.message

        if user_id and user_message:
            logger.info(f"Creating background task for user_id={user_id}")
            asyncio.create_task(process_message(bot_id, user_id, user_message))
        else:
            logger.warning(
                f"Missing user_id or message: user_id={user_id}, message={user_message}"
            )

    return {"status": "ok"}


# -----------------------------
# Include router
# -----------------------------
app.include_router(zalo_router)
