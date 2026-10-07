import asyncio
import random
import time

import httpx

from config.settings import settings


def _should_retry(status_code: int) -> bool:
    return status_code in (429, 502, 503, 504)


async def call_llm(messages: list[dict], logger) -> str | None:
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
    }

    for attempt in range(1, settings.MAX_RETRIES + 1):
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
                response = await client.post(
                    settings.OPENAI_API_URL, json=payload, headers=headers
                )
            duration = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("llm_call_success", extra={
                    "attempt": attempt,
                    "duration_ms": round(duration, 2),
                    "response_len": len(content),
                })
                return content

            if _should_retry(response.status_code):
                if attempt < settings.MAX_RETRIES:
                    delay = min(1 * 2 ** (attempt - 1), 10) + random.uniform(-0.5, 0.5)
                    logger.info("llm_call_retry", extra={
                        "attempt": attempt,
                        "status_code": response.status_code,
                        "next_delay": round(delay, 2),
                    })
                    await asyncio.sleep(max(delay, 0.1))
                    continue
                else:
                    logger.info("llm_call_failed", extra={
                        "attempt": attempt,
                        "status_code": response.status_code,
                        "fallback_used": True,
                    })
                    return None
            else:
                logger.info("llm_call_failed", extra={
                    "attempt": attempt,
                    "status_code": response.status_code,
                    "fallback_used": True,
                })
                return None

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            duration = (time.perf_counter() - start) * 1000
            if attempt < settings.MAX_RETRIES:
                delay = min(1 * 2 ** (attempt - 1), 10) + random.uniform(-0.5, 0.5)
                logger.info("llm_call_retry", extra={
                    "attempt": attempt,
                    "error": type(e).__name__,
                    "duration_ms": round(duration, 2),
                    "next_delay": round(delay, 2),
                })
                await asyncio.sleep(max(delay, 0.1))
                continue
            else:
                logger.info("llm_call_failed", extra={
                    "attempt": attempt,
                    "error": type(e).__name__,
                    "fallback_used": True,
                })
                return None

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.info("llm_call_failed", extra={
                "attempt": attempt,
                "error": type(e).__name__,
                "duration_ms": round(duration, 2),
                "fallback_used": True,
            })
            return None

    return None