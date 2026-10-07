from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Текст для суммаризации",
    )


class ChatResponse(BaseModel):
    response: str
    cached: bool
    model: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int