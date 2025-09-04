# app/core/config.py
from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import DirectoryPath, AnyHttpUrl
import os

class Settings(BaseSettings):
    # API
    APP_NAME: str = "UCDB Chat"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # LLM
    LLM_BASE_URL: AnyHttpUrl = "http://localhost:8080/v1"
    EMBEDDING_API_URL: AnyHttpUrl = "http://localhost:8081/embedding"
    MAX_TOKENS: int = 10240
    TEMPERATURE: float = 0.8
    TOP_P: float = 0.9
    REPETITION_PENALTY: float = 1.1

    # RAG
    CHUNK_SIZE: int = 812
    CHUNK_OVERLAP: int = 64
    RETRIEVAL_K: int = 4

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PDF_DIR: DirectoryPath
    VECTORSTORE_DIR: str
    STATIC_DIR: DirectoryPath

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
        return os.path.join(self.BASE_DIR, "pdfs")

    @property
    def static_path(self) -> str:
        return os.path.join(self.BASE_DIR, "static")

settings = Settings(
    PDF_DIR=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "pdfs"),
    VECTORSTORE_DIR=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "embeddings"),
    STATIC_DIR=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")
)