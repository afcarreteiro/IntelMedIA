import base64
import binascii
from dataclasses import dataclass

import numpy as np

from app.config import settings
from app.services.hf_runtime import has_cuda_runtime
from app.services.runpod_asr import runpod_asr_service

try:
    from faster_whisper import WhisperModel
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    WhisperModel = None

try:
    from qwen_asr import Qwen3ASRModel
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    Qwen3ASRModel = None


WHISPER_LANGUAGE_HINTS = {
    "pt-PT": "pt",
    "en-GB": "en",
    "fr-FR": "fr",
    "es-ES": "es",
    "de-DE": "de",
    "it-IT": "it",
    "uk-UA": "uk",
    "ar": "ar",
    "hi-IN": "hi",
    "bn-BD": "bn",
    "ur-PK": "ur",
    "zh-CN": "zh",
}

QWEN_LANGUAGE_HINTS = {
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
        self._whisper_model = None
        self._qwen_model = None
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
        return self.transcribe_samples(merged_audio, sample_rate, language_code)

    def transcribe_samples(self, samples: np.ndarray, sample_rate: int, language_code: str) -> ASRTranscription:
        if samples.size == 0:
            return ASRTranscription(
                text="",
                detected_language=None,
                engine="empty_audio",
                uncertainty_reasons=["Nenhum audio foi capturado para esta intervencao."],
            )

        if settings.asr_backend == "runpod_ws":
            return self._transcribe_with_runpod(samples, sample_rate, language_code)

        if settings.asr_backend == "qwen_legacy":
            return self._transcribe_with_qwen(samples, sample_rate, language_code)

        return self._transcribe_with_whisper(samples, sample_rate, language_code)

    def current_engine_label(self) -> str:
        if settings.asr_backend == "runpod_ws":
            return "runpod:qwen3-asr"
        if settings.asr_backend == "qwen_legacy":
            return settings.asr_model_id
        return settings.whisper_model_id

    def is_realtime_ready(self) -> bool:
        if settings.asr_backend == "runpod_ws":
            return True
        return has_cuda_runtime() or not settings.require_gpu_for_realtime

    def preload(self) -> tuple[bool, str | None]:
        if settings.asr_backend == "runpod_ws":
            return runpod_asr_service.preload()
        if settings.asr_backend == "qwen_legacy":
            model = self._ensure_qwen_model()
        else:
            model = self._ensure_whisper_model()
        return model is not None, self._load_error

    def _transcribe_with_runpod(self, samples: np.ndarray, sample_rate: int, language_code: str) -> ASRTranscription:
        text, detected_language, engine, uncertainty_reasons = runpod_asr_service.transcribe_samples(
            samples=samples,
            sample_rate=sample_rate,
            language_code=language_code,
        )
        return ASRTranscription(
            text=text,
            detected_language=detected_language,
            engine=engine if text or uncertainty_reasons else "runpod:qwen3-asr",
            uncertainty_reasons=uncertainty_reasons,
        )

    def _transcribe_with_whisper(self, samples: np.ndarray, sample_rate: int, language_code: str) -> ASRTranscription:
        model = self._ensure_whisper_model()
        if model is None:
            return ASRTranscription(
                text="",
                detected_language=None,
                engine="asr_unavailable",
                uncertainty_reasons=[self._load_error or "O modelo ASR nao esta disponivel."],
            )

        language_hint = WHISPER_LANGUAGE_HINTS.get(language_code)
        try:
            segments, info = model.transcribe(
                samples.astype(np.float32),
                language=language_hint,
                beam_size=1,
                best_of=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
            reasons = [] if text else ["O modelo ASR nao devolveu texto para este audio."]
            return ASRTranscription(
                text=text,
                detected_language=getattr(info, "language", language_hint),
                engine=self._loaded_model_id or settings.whisper_model_id,
                uncertainty_reasons=reasons,
            )
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            return ASRTranscription(
                text="",
                detected_language=None,
                engine=self._loaded_model_id or settings.whisper_model_id,
                uncertainty_reasons=[f"Falha na transcricao ASR: {exc}"],
            )

    def _transcribe_with_qwen(self, samples: np.ndarray, sample_rate: int, language_code: str) -> ASRTranscription:
        model = self._ensure_qwen_model()
        if model is None:
            return ASRTranscription(
                text="",
                detected_language=None,
                engine="asr_unavailable",
                uncertainty_reasons=[self._load_error or "O modelo ASR nao esta disponivel."],
            )

        language_hint = QWEN_LANGUAGE_HINTS.get(language_code)
        try:
            results = model.transcribe(
                audio=(samples, sample_rate),
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

    def _ensure_whisper_model(self):
        if self._whisper_model is not None:
            return self._whisper_model
        if WhisperModel is None:
            self._load_error = "A dependencia faster-whisper nao esta instalada."
            return None

        try:
            device = "cuda" if has_cuda_runtime() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            self._whisper_model = WhisperModel(
                settings.whisper_model_id,
                device=device,
                compute_type=compute_type,
            )
            self._loaded_model_id = settings.whisper_model_id
            self._load_error = None
            return self._whisper_model
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            self._load_error = str(exc)
            return None

    def _ensure_qwen_model(self):
        if self._qwen_model is not None:
            return self._qwen_model
        if Qwen3ASRModel is None:
            self._load_error = "A dependencia qwen-asr nao esta instalada."
            return None

        candidate_ids = [settings.asr_model_id]
        if settings.asr_fallback_model_id not in candidate_ids:
            candidate_ids.append(settings.asr_fallback_model_id)

        last_error: str | None = None
        for model_id in candidate_ids:
            try:
                self._qwen_model = Qwen3ASRModel.from_pretrained(
                    model_id,
                    max_new_tokens=settings.asr_max_new_tokens,
                    max_inference_batch_size=4,
                )
                self._loaded_model_id = model_id
                self._load_error = None
                return self._qwen_model
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
