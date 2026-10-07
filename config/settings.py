import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "600"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))
    OPENAI_API_URL: str = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    FALLBACK_RESPONSE: str = "Сервис временно недоступен. Пожалуйста, попробуйте позже."


settings = Settings()