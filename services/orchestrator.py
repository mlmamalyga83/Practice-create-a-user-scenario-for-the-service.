import time
from config.settings import settings
from cache.ttl_cache import TTLCache
from llm.prompts import build_messages, SYSTEM_PROMPT_SUMMARIZATION
from llm.client import call_llm

cache = TTLCache(ttl=settings.CACHE_TTL)


async def process_message(message: str, logger) -> dict:
    total_start = time.perf_counter()

    cache_result = cache.get(
        message,
        settings.LLM_MODEL,
        settings.LLM_TEMPERATURE,
        SYSTEM_PROMPT_SUMMARIZATION,
    )

    if cache_result is not None:
        cached_value, ttl_remaining = cache_result
        total_duration = (time.perf_counter() - total_start) * 1000
        logger.info("cache_hit", extra={
            "key_hash": cache._make_key(
                message, settings.LLM_MODEL,
                settings.LLM_TEMPERATURE,
                SYSTEM_PROMPT_SUMMARIZATION,
            )[:12],
            "ttl_remaining": round(ttl_remaining),
            "duration_ms": round(total_duration, 2),
        })
        logger.info("response_sent", extra={
            "status_code": 200,
            "cached": True,
            "duration_ms": round(total_duration, 2),
        })
        return {
            "response": cached_value,
            "cached": True,
            "model": settings.LLM_MODEL,
        }

    logger.info("cache_miss", extra={
        "key_hash": cache._make_key(
            message, settings.LLM_MODEL,
            settings.LLM_TEMPERATURE,
            SYSTEM_PROMPT_SUMMARIZATION,
        )[:12],
    })

    messages = build_messages(message)
    logger.info("prompt_built", extra={
        "system_prompt_len": len(messages[0]["content"]),
        "user_prompt_len": len(messages[1]["content"]),
    })

    llm_result = await call_llm(messages, logger)

    if llm_result is None:
        total_duration = (time.perf_counter() - total_start) * 1000
        logger.info("post_processing", extra={
            "raw_len": 0,
            "cleaned_len": 0,
            "is_valid": False,
        })
        logger.info("response_sent", extra={
            "status_code": 503,
            "cached": False,
            "fallback": True,
            "duration_ms": round(total_duration, 2),
        })
        return {
            "response": settings.FALLBACK_RESPONSE,
            "cached": False,
            "model": "fallback",
        }

    cleaned = llm_result.strip()
    is_valid = len(cleaned) > 0
    logger.info("post_processing", extra={
        "raw_len": len(llm_result),
        "cleaned_len": len(cleaned),
        "is_valid": is_valid,
    })

    if not is_valid:
        total_duration = (time.perf_counter() - total_start) * 1000
        logger.info("response_sent", extra={
            "status_code": 503,
            "cached": False,
            "fallback": True,
            "duration_ms": round(total_duration, 2),
        })
        return {
            "response": settings.FALLBACK_RESPONSE,
            "cached": False,
            "model": "fallback",
        }

    cache.set(
        message,
        settings.LLM_MODEL,
        settings.LLM_TEMPERATURE,
        SYSTEM_PROMPT_SUMMARIZATION,
        cleaned,
    )

    total_duration = (time.perf_counter() - total_start) * 1000
    logger.info("response_sent", extra={
        "status_code": 200,
        "cached": False,
        "duration_ms": round(total_duration, 2),
    })

    return {
        "response": cleaned,
        "cached": False,
        "model": settings.LLM_MODEL,
    }