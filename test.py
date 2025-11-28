import os
import asyncio
from src.utils import call_dify_workflow


async def test_multiple_workflows():
    tasks = [
        call_dify_workflow("bot1", "Xin chào từ workflow 1"),
        call_dify_workflow("bot2", "Xin chào từ workflow 2"),
        call_dify_workflow("bot3", "Xin chào từ workflow 3"),
    ]
    results = await asyncio.gather(*tasks)
    for i, text in enumerate(results, 1):
        print(f"[workflow_{i}] Response:\n{text}")


if __name__ == "__main__":
    asyncio.run(test_multiple_workflows())
