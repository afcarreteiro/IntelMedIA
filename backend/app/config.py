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
    asr_backend: str = "runpod_ws"
    mt_backend: str = "nllb"

    hf_token: str = ""
    model_device_map: str = "auto"
    model_dtype: str = "auto"
    use_huggingface_models: bool = True
    require_gpu_for_realtime: bool = True
    asr_model_id: str = "Qwen/Qwen3-ASR-1.7B"
    asr_fallback_model_id: str = "Qwen/Qwen3-ASR-1.7B"
    whisper_model_id: str = "openai/whisper-large-v3-turbo"
    nllb_model_id: str = "facebook/nllb-200-distilled-600M"
    mt_model_id: str = "facebook/nllb-200-distilled-600M"
    soap_model_id: str = "meta-llama/Llama-3.1-8B-Instruct"
    asr_max_new_tokens: int = 256
    runpod_asr_ws_url: str = ""
    runpod_asr_ready_url: str = ""
    runpod_asr_api_key: str = ""
    runpod_asr_connect_timeout_s: float = 5.0
    runpod_asr_partial_timeout_s: float = 2.0
    runpod_asr_final_timeout_s: float = 10.0
    mt_max_new_tokens: int = 220
    soap_max_new_tokens: int = 700
    stream_sample_rate: int = 16000
    stream_chunk_ms: int = 160
    stream_partial_interval_ms: int = 480
    stream_translation_debounce_ms: int = 350
    stream_endpoint_silence_ms: int = 700
    stream_max_turn_ms: int = 6000
    stream_context_window_ms: int = 1600
    stream_vad_threshold: float = 0.012


settings = Settings()
