# app/core/config.py - Versão com Penalidade de Repetição Aumentada

from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import DirectoryPath, AnyHttpUrl
import os
import secrets

class Settings(BaseSettings):
    # API
    APP_NAME: str = "UCDB Chat"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_hex(32)

    # LLM
    LLM_BASE_URL: AnyHttpUrl = "http://localhost:8080/v1"
    EMBEDDING_API_URL: AnyHttpUrl = "http://localhost:8081/embedding"
    MAX_TOKENS: int = 15500
    TEMPERATURE: float = 0.85  # Reduzir um pouco a temperatura pode ajudar na consistência
    TOP_P: float = 0.9
    REPETITION_PENALTY: float = 1  # <-- PREVENIR LOOPS

    # RAG
    CHUNK_SIZE: int = 812
    CHUNK_OVERLAP: int = 64
    RETRIEVAL_K: int = 7 # Aumentar ligeiramente para mais contexto

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def vectorstore_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "embeddings")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def pdf_path(self) -> str:
        path = os.path.join(self.BASE_DIR, "pdfs")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def static_path(self) -> str:
        return os.path.join(self.BASE_DIR, "static")

settings = Settings()