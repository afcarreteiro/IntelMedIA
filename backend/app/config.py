from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INTELMEDIA_",
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

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
    translation_provider: str = "huggingface_qwen"

    hf_token: str = ""
    model_device_map: str = "auto"
    model_dtype: str = "auto"
    use_huggingface_models: bool = True
    asr_model_id: str = "Qwen/Qwen3.5-ASR-1.7B"
    asr_fallback_model_id: str = "Qwen/Qwen3-ASR-1.7B"
    mt_model_id: str = "Qwen/Qwen3.5-4B"
    soap_model_id: str = "meta-llama/Llama-3.1-8B-Instruct"
    asr_max_new_tokens: int = 256
    mt_max_new_tokens: int = 220
    soap_max_new_tokens: int = 700


settings = Settings()
