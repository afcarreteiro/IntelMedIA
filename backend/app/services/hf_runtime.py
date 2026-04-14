import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

from app.config import settings

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    torch = None


@dataclass
class RuntimeConfig:
    token: str | None
    device_map: str
    torch_dtype: object | None


def get_runtime_config() -> RuntimeConfig:
    token = settings.hf_token or os.getenv("HF_TOKEN") or None
    return RuntimeConfig(
        token=token,
        device_map=settings.model_device_map,
        torch_dtype=_resolve_torch_dtype(),
    )


def _resolve_torch_dtype():
    if torch is None:
        return None

    if settings.model_dtype == "float16":
        return torch.float16
    if settings.model_dtype == "bfloat16":
        return torch.bfloat16
    if settings.model_dtype == "float32":
        return torch.float32

    if torch.cuda.is_available():
        return torch.bfloat16
    return torch.float32
