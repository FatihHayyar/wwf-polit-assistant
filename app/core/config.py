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

    # Verification başarılı olduktan sonra frontend'e yönlendirme
    frontend_url: str = "http://localhost:3000"
    
    # POST /api/v1/sync/run icin yonetici anahtari.
    sync_api_key: str | None = None

    # E-mail / verification
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "WWF Polit-Assistant"

    # Frontend'e gönderilecek doğrulama linkinin temel adresi.
    # Örn: https://polit-assistant.example.ch
    verification_base_url: str = "http://localhost:8000"

    # Verification token geçerlilik süresi.
    email_verification_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()