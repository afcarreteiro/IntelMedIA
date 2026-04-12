from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://intelmedia:intelmedia@localhost:5432/intelmedia"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"

    model_config = SettingsConfigDict(env_prefix="INTELMEDIA_", extra="ignore")


settings = Settings()
