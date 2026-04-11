from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Project root directory (one level above backend/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    # -----------------------------
    # DATABASE
    # -----------------------------
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/justiceai"

    # -----------------------------
    # EMBEDDINGS / VECTOR DB
    # -----------------------------
    EMBEDDING_MODEL: str = "multi-qa-MiniLM-L6-cos-v1"
    CHROMA_DB_PATH: str = str(BASE_DIR / "chroma_store")
    TOP_K_RESULTS: int = 5

    # -----------------------------
    # GEMINI (optional fallback)
    # -----------------------------
    GEMINI_API_KEY: str = ""

    # -----------------------------
    # SAMBANOVA / DEEPSEEK LLM
    # -----------------------------
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    LLM_MODEL: str = "DeepSeek-V3-0324"

    # Load environment variables from .env
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
