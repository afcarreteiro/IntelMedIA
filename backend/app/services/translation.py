from dataclasses import dataclass

from app.config import settings
from app.services.hf_runtime import get_runtime_config

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    AutoModelForCausalLM = None
    AutoTokenizer = None


LANGUAGE_NAMES = {
    "pt-PT": "Portuguese from Portugal",
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
    "zh-CN": "Simplified Chinese",
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

        if not settings.use_huggingface_models:
            return self._fallback_result(source_text, "O pipeline Hugging Face esta desativado.")

        tokenizer, model = self._ensure_model()
        if tokenizer is None or model is None:
            return self._fallback_result(source_text, self._load_error or "O modelo MT nao esta disponivel.")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are IntelMedIA's medical translation engine. "
                    "Translate the clinician or patient utterance faithfully. "
                    "Preserve negation, medication names, numbers, symptoms, and uncertainty. "
                    "Return only the translation text with no explanations."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Source language: {LANGUAGE_NAMES.get(source_language, source_language)}\n"
                    f"Target language: {LANGUAGE_NAMES.get(target_language, target_language)}\n"
                    f"Utterance:\n{source_text.strip()}"
                ),
            },
        ]

        try:
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = tokenizer(prompt, return_tensors="pt")
            if hasattr(model, "device") and str(model.device) != "cpu":
                inputs = {name: tensor.to(model.device) for name, tensor in inputs.items()}

            output = model.generate(
                **inputs,
                max_new_tokens=settings.mt_max_new_tokens,
                do_sample=False,
            )
            prompt_length = inputs["input_ids"].shape[1]
            generated_tokens = output[0][prompt_length:]
            translated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
            if not translated_text:
                return self._fallback_result(source_text, "O modelo MT nao devolveu traducao.")

            return TranslationResult(
                translated_text=translated_text,
                engine=settings.mt_model_id,
                uncertainty_reasons=[],
            )
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            return self._fallback_result(source_text, f"Falha na traducao MT: {exc}")

    def _ensure_model(self):
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model
        if AutoTokenizer is None or AutoModelForCausalLM is None:
            self._load_error = "A dependencia transformers nao esta instalada."
            return None, None

        runtime = get_runtime_config()
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.mt_model_id,
                token=runtime.token,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.mt_model_id,
                token=runtime.token,
                device_map=runtime.device_map,
                torch_dtype=runtime.torch_dtype,
            )
            self._load_error = None
            return self._tokenizer, self._model
        except Exception as exc:  # pragma: no cover - hardware/runtime dependent
            self._load_error = str(exc)
            return None, None

    def _fallback_result(self, source_text: str, reason: str) -> TranslationResult:
        return TranslationResult(
            translated_text=source_text,
            engine="qwen_mt_fallback",
            uncertainty_reasons=[
                reason,
                "A traducao deve ser revista pelo clinico.",
            ],
        )


translation_service = TranslationService()
