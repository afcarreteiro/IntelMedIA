from dataclasses import dataclass

from app.config import settings
from app.services.hf_runtime import get_runtime_config

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    torch = None

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    AutoModelForSeq2SeqLM = None
    AutoTokenizer = None


NLLB_LANGUAGE_CODES = {
    "pt-PT": "por_Latn",
    "en-GB": "eng_Latn",
    "fr-FR": "fra_Latn",
    "es-ES": "spa_Latn",
    "de-DE": "deu_Latn",
    "it-IT": "ita_Latn",
    "uk-UA": "ukr_Cyrl",
    "ar": "arb_Arab",
    "hi-IN": "hin_Deva",
    "bn-BD": "ben_Beng",
    "ur-PK": "urd_Arab",
    "zh-CN": "zho_Hans",
}


@dataclass
class TranslationResult:
    translated_text: str
    engine: str
    uncertainty_reasons: list[str]

    @property
    def is_uncertain(self) -> bool:
        return bool(self.uncertainty_reasons)


class TranslationService:
    def __init__(self):
        self._tokenizer = None
        self._model = None
        self._load_error: str | None = None
        self._device: str = "cpu"

    def translate(self, source_text: str, source_language: str, target_language: str) -> TranslationResult:
        if source_language == target_language:
            return TranslationResult(
                translated_text=source_text,
                engine="identity",
                uncertainty_reasons=[],
            )

        if not source_text.strip():
            return TranslationResult(
                translated_text="",
                engine="empty_input",
                uncertainty_reasons=["Nao foi fornecido texto para traducao."],
            )

        if settings.mt_backend != "nllb":
            return self._fallback_result(source_text, "O backend MT configurado nao esta suportado.")

        if not settings.use_huggingface_models:
            return self._fallback_result(source_text, "O pipeline Hugging Face esta desativado.")

        mapped_source = NLLB_LANGUAGE_CODES.get(source_language)
        mapped_target = NLLB_LANGUAGE_CODES.get(target_language)
        if mapped_source is None or mapped_target is None:
            return self._fallback_result(source_text, "O par de idiomas nao esta mapeado para o modelo MT.")

        tokenizer, model = self._ensure_model()
        if tokenizer is None or model is None:
            return self._fallback_result(source_text, self._load_error or "O modelo MT nao esta disponivel.")

        try:
            tokenizer.src_lang = mapped_source
            inputs = tokenizer(source_text.strip(), return_tensors="pt")
            if self._device != "cpu":
                inputs = {name: tensor.to(self._device) for name, tensor in inputs.items()}

            generated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(mapped_target),
                max_new_tokens=settings.mt_max_new_tokens,
                do_sample=False,
            )
            translated_text = tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
            )[0].strip()
            if not translated_text:
                return self._fallback_result(source_text, "O modelo MT nao devolveu traducao.")

            return TranslationResult(
                translated_text=translated_text,
                engine=settings.nllb_model_id,
                uncertainty_reasons=[],
            )
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            return self._fallback_result(source_text, f"Falha na traducao MT: {exc}")

    def preload(self) -> tuple[bool, str | None]:
        tokenizer, model = self._ensure_model()
        return tokenizer is not None and model is not None, self._load_error

    def _ensure_model(self):
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model
        if AutoTokenizer is None or AutoModelForSeq2SeqLM is None:
            self._load_error = "A dependencia transformers nao esta instalada."
            return None, None

        runtime = get_runtime_config()
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.nllb_model_id,
                token=runtime.token,
            )
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                settings.nllb_model_id,
                token=runtime.token,
                dtype=runtime.dtype,
            )
            self._device = runtime.device
            if self._device != "cpu" and torch is not None:
                self._model = self._model.to(self._device)
            self._load_error = None
            return self._tokenizer, self._model
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            self._load_error = str(exc)
            return None, None

    def _fallback_result(self, source_text: str, reason: str) -> TranslationResult:
        return TranslationResult(
            translated_text=source_text,
            engine="mt_fallback",
            uncertainty_reasons=[
                reason,
                "A traducao deve ser revista pelo clinico.",
            ],
        )


translation_service = TranslationService()
