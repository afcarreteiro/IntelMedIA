import base64
import binascii
from dataclasses import dataclass

import numpy as np

from app.config import settings
from app.services.hf_runtime import get_runtime_config

try:
    from qwen_asr import Qwen3ASRModel
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    Qwen3ASRModel = None


LANGUAGE_HINTS = {
    "pt-PT": "Portuguese",
    "en-GB": "English",
    "fr-FR": "French",
    "es-ES": "Spanish",
    "de-DE": "German",
    "it-IT": "Italian",
    "uk-UA": "Ukrainian",
    "ar": "Arabic",
    "hi-IN": "Hindi",
    "bn-BD": "Bengali",
    "ur-PK": "Urdu",
    "zh-CN": "Chinese",
}


@dataclass
class ASRTranscription:
    text: str
    detected_language: str | None
    engine: str
    uncertainty_reasons: list[str]


class ASRPipelineService:
    def __init__(self):
        self._model = None
        self._loaded_model_id: str | None = None
        self._load_error: str | None = None

    def transcribe_merged_chunks(self, chunks: list[dict], language_code: str) -> ASRTranscription:
        if not chunks:
            return ASRTranscription(
                text="",
                detected_language=None,
                engine="empty_audio",
                uncertainty_reasons=["Nenhum audio foi capturado para esta intervencao."],
            )

        merged_audio, sample_rate = self._merge_chunks(chunks)
        model = self._ensure_model()
        if model is None:
            return ASRTranscription(
                text="",
                detected_language=None,
                engine="asr_unavailable",
                uncertainty_reasons=[self._load_error or "O modelo ASR nao esta disponivel."],
            )

        language_hint = LANGUAGE_HINTS.get(language_code)
        try:
            results = model.transcribe(
                audio=(merged_audio, sample_rate),
                language=language_hint,
            )
            result = results[0]
            if isinstance(result, dict):
                text = (result.get("text", "") or "").strip()
                detected_language = result.get("language")
            else:
                text = (getattr(result, "text", "") or "").strip()
                detected_language = getattr(result, "language", None)
            reasons = [] if text else ["O modelo ASR nao devolveu texto para este audio."]
            return ASRTranscription(
                text=text,
                detected_language=detected_language,
                engine=self._loaded_model_id or settings.asr_model_id,
                uncertainty_reasons=reasons,
            )
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            return ASRTranscription(
                text="",
                detected_language=None,
                engine=self._loaded_model_id or settings.asr_model_id,
                uncertainty_reasons=[f"Falha na transcricao ASR: {exc}"],
            )

    def _ensure_model(self):
        if self._model is not None or not settings.use_huggingface_models:
            return self._model
        if Qwen3ASRModel is None:
            self._load_error = "A dependencia qwen-asr nao esta instalada."
            return None

        runtime = get_runtime_config()
        candidate_ids = [settings.asr_model_id]
        if settings.asr_fallback_model_id not in candidate_ids:
            candidate_ids.append(settings.asr_fallback_model_id)

        last_error: str | None = None
        for model_id in candidate_ids:
            try:
                self._model = Qwen3ASRModel.from_pretrained(
                    model_id,
                    token=runtime.token,
                    dtype=runtime.torch_dtype,
                    device_map=runtime.device_map,
                    max_new_tokens=settings.asr_max_new_tokens,
                    max_inference_batch_size=4,
                )
                self._loaded_model_id = model_id
                self._load_error = None
                return self._model
            except Exception as exc:  # pragma: no cover - hardware/runtime dependent
                last_error = str(exc)

        self._load_error = last_error or "Nao foi possivel carregar o modelo ASR."
        return None

    def _merge_chunks(self, chunks: list[dict]) -> tuple[np.ndarray, int]:
        ordered = sorted(chunks, key=lambda chunk: chunk["sequence"])
        sample_rate = ordered[0]["sample_rate"]
        merged: list[np.ndarray] = []

        for index, chunk in enumerate(ordered):
            pcm = self._decode_chunk(chunk["payload_base64"])
            if index == 0:
                merged.append(pcm)
                continue

            overlap_samples = int(chunk["overlap_ms"] * sample_rate / 1000)
            if overlap_samples > 0 and overlap_samples < len(pcm):
                merged.append(pcm[overlap_samples:])
            else:
                merged.append(pcm)

        combined = np.concatenate(merged) if merged else np.array([], dtype=np.float32)
        return combined, sample_rate

    def _decode_chunk(self, payload_base64: str) -> np.ndarray:
        try:
            raw_bytes = base64.b64decode(payload_base64)
        except (ValueError, binascii.Error):
            return np.array([], dtype=np.float32)

        pcm16 = np.frombuffer(raw_bytes, dtype=np.int16)
        return pcm16.astype(np.float32) / 32768.0


asr_pipeline_service = ASRPipelineService()
