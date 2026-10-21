from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WWF Polit-Assistant API"
    app_version: str = "0.1.0"
    database_url: str


    # JWT / passwordless authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Frontend address used for redirects after successful verification
    frontend_url: str = "http://localhost:3000"
    
    # Administrator key for the /api/v1/sync endpoints.
    sync_api_key: str | None = None

    # E-mail / verification
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_starttls: bool = True
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "WWF Polit-Assistant"

    # Public base URL used in verification and login links.
    # Example: https://polit-assistant.example.ch
    verification_base_url: str = "http://localhost:8000"

    # Lifetime of verification and login tokens.
    email_verification_minutes: int = 30

    # Limits for email-sending and token endpoints (see app/core/rate_limit.py).
    rate_limit_enabled: bool = True

    # Enables the demo-only endpoint that creates a sample affair and sends
    # notifications. Never enable this for a production database.
    demo_mode: bool = False
    # Web mailbox of the demo (Mailpit) shown after a test notification.
    demo_mailbox_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
