"""
Application configuration loaded from environment variables.

Uses pydantic-settings BaseSettings — values are read from the .env file
(or real environment). All secrets stay server-side only.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/interviewpro"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/interviewpro_test"

    # ── JWT / Auth ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-to-a-random-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Cookie settings ───────────────────────────────────────────────────────
    # COOKIE_SECURE: False in development (HTTP), True in production (HTTPS)
    # COOKIE_SAMESITE: "lax" for most cases; "none" only when cross-site + Secure=True
    COOKIE_SECURE: bool = False          # Set True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"         # "lax" works for same-origin dev setup
    COOKIE_DOMAIN: str | None = None     # None = browser default (current domain)

    # ── IBM Granite / watsonx.ai ──────────────────────────────────────────────
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    GRANITE_MODEL_ID: str = "ibm/granite-13b-instruct-v2"
    GRANITE_EMBEDDING_MODEL: str = "ibm/slate-125m-english-rtrvr"

    # ── CORS ──────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────────────────────────────────
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


# Single shared instance — import this everywhere
settings = Settings()
