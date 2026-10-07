import logging
import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api.models import ChatRequest, ChatResponse, ErrorResponse
from services.orchestrator import process_message

router = APIRouter()
logger = logging.getLogger("llm_service")


@router.post("/chat")
async def chat(request: ChatRequest):
    log = logger
    log.info("request_received", extra={
        "message_len": len(request.message),
        "message_preview": request.message[:50],
    })

    log.info("validation_passed", extra={
        "message_len": len(request.message),
    })

    try:
        result = await process_message(request.message, log)

        if result["model"] == "fallback":
            return JSONResponse(
                status_code=503,
                content=ErrorResponse(
                    error="SERVICE_UNAVAILABLE",
                    detail="Сервис временно недоступен, попробуйте позже.",
                    status_code=503,
                ).model_dump(),
            )

        return ChatResponse(**result)

    except Exception as e:
        log.info("internal_error", extra={
            "error": type(e).__name__,
            "detail": str(e),
            "traceback": traceback.format_exc(),
        })
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                detail="Внутренняя ошибка сервера.",
                status_code=500,
            ).model_dump(),
        )