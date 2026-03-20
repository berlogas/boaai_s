from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_TIMEOUT: int = 3000  # Таймаут для запросов к Ollama (секунды) - 50 минут для слабых ПК
    DEFAULT_LLM_MODEL: str = "llama3.1:8b"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"
    MAX_SESSIONS_PER_USER: int = 10
    MAX_DOCS_PER_SESSION: int = 50
    MAX_STORAGE_MB_PER_SESSION: int = 500
    MAX_PROJECTS_PER_SESSION: int = 5
    SESSION_TTL_DAYS: int = 90
    HEARTBEAT_INTERVAL_MINUTES: int = 5

    DATA_PATH: str = "/app/data"
    GLOBAL_INDEX_PATH: str = "/app/global_index"
    UPLOADS_PATH: str = "/app/uploads"

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

os.makedirs(settings.DATA_PATH, exist_ok=True)
os.makedirs(settings.GLOBAL_INDEX_PATH, exist_ok=True)
os.makedirs(settings.UPLOADS_PATH, exist_ok=True)