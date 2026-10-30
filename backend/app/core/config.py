"""
TruthLens - Application Configuration
Uses pydantic-settings to manage environment variables with validated defaults.
"""
import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TruthLens"
    PROJECT_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security & JWT
    SECRET_KEY: str = "truthlens-dev-secret-key-32-chars-long-secure-random!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./truthlens.db"

    # Local AI & Ollama Configuration
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    OLLAMA_TIMEOUT_SECONDS: int = 60
    OLLAMA_NUM_THREADS: int = 4

    # Search Services Configuration
    SEARXNG_URL: str = "http://127.0.0.1:8080"
    GDELT_ENABLED: bool = True
    RSS_ENABLED: bool = True

    # NLI Verification Configuration
    NLI_MODEL_NAME: str = "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
    NLI_ENTAILMENT_THRESHOLD: float = 0.65
    NLI_CONTRADICTION_THRESHOLD: float = 0.65
    NLI_MAX_PASSAGES_PER_CLAIM: int = 5

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # ML Artifacts
    ML_ARTIFACTS_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "artifacts"
    )

    # URL Extraction Security
    REQUEST_TIMEOUT_SECONDS: int = 10
    MAX_RESPONSE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

