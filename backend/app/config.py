from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INTELMEDIA_", extra="ignore")

    app_name: str = "IntelMedIA API"
    debug: bool = False

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    database_url: str = "sqlite:///./intelmedia.db"
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    transcript_retention: str = "ephemeral_memory_only"
    region: str = "pt-PT"
    translation_provider: str = "demo"


settings = Settings()
