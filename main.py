import json
import logging
import os
import sys
import traceback
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routes import router


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.") +
                         f"{record.created % 1:.3f}".split(".")[1].ljust(3, "0") + "Z",
            "level": record.levelname,
            "event": record.getMessage(),
        }
        skip_keys = {
            "timestamp", "level", "event", "name", "msg", "args",
            "levelno", "levelname", "pathname", "filename", "module",
            "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message",
        }
        for key, value in record.__dict__.items():
            if key not in skip_keys and not key.startswith("_"):
                log_obj[key] = value
        if record.exc_info and record.exc_info[0]:
            log_obj["traceback"] = "".join(
                traceback.format_exception(*record.exc_info)
            ).strip()
        return json.dumps(log_obj, ensure_ascii=False, default=str)


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("llm_service")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JsonFormatter())

    file_handler = logging.FileHandler(
        f"logs/service_{datetime.now().strftime('%Y-%m-%d')}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").addHandler(console_handler)

    return logger


app = FastAPI(title="LLM Summarizer")
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger = logging.getLogger("llm_service")
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = ".".join(first_error.get("loc", []))
    msg = first_error.get("msg", "Ошибка валидации")
    detail = f"Поле '{field}': {msg}" if field else msg
    logger.info("validation_failed", extra={
        "error": "VALIDATION_ERROR",
        "detail": detail,
        "status_code": 422,
    })
    return JSONResponse(
        status_code=422,
        content={"error": "VALIDATION_ERROR", "detail": detail, "status_code": 422},
    )


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)