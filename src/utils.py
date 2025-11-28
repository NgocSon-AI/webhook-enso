import json
from typing import Any, Dict, Optional
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DIFY_API_KEY = os.getenv("DIFY_TOKEN")

ZALO_OA_TOKEN = os.getenv("ZALO_ACCESS_TOKEN")

WORKFLOWS = {
    "bot1": {"id": os.getenv("WORKFLOW1_ID"), "key": os.getenv("WORKFLOW1_KEY")},
    # "bot2": {"id": os.getenv("WORKFLOW2_ID"), "key": os.getenv("WORKFLOW2_KEY")},
    # "bot3": {"id": os.getenv("WORKFLOW3_ID"), "key": os.getenv("WORKFLOW3_KEY")},
}


async def call_dify_workflow(
    bot_id: str, user_input: str, session: Optional[Dict[str, Any]] = None
) -> str:
    workflow = WORKFLOWS.get(bot_id)
    if not workflow:
        raise ValueError(f"Unknown bot_id: {bot_id}")

    url = f"https://chatbot.ai-enso.com/v1/workflows/run"

    headers = {
        "Authorization": f"Bearer {workflow['key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {"query": user_input},
        "response_mode": "blocking",
        "user": f"{bot_id}_user_001",
    }

    if session:
        payload["context"] = session.get("context", {})

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Lấy text trả về
    try:
        outputs = data.get("data", {}).get("outputs")
        if isinstance(outputs, dict):
            text = outputs.get("text", "")
            return text
        if isinstance(outputs, str):
            return outputs
        if isinstance(outputs, list) and len(outputs) > 0:
            first = outputs[0]
            if isinstance(first, dict):
                return first.get("text", "")
            return bot_id, str(first)
    except Exception:
        pass

    return "Xin lỗi, hệ thống tạm thời không trả lời được."


async def send_zalo_message(user_id: str, text: str):
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {
        "Content-Type": "application/json",
        "access_token": ZALO_OA_TOKEN,
    }
    payload = {
        "recipient": {"user_id": user_id},
        "message": {"text": text},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
