import json
import re

from app.config import settings
from app.schemas.session import SoapResponse, TranscriptSegment
from app.services.hf_runtime import get_runtime_config

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    torch = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    AutoModelForCausalLM = None
    AutoTokenizer = None


class SoapGenerationService:
    def __init__(self):
        self._tokenizer = None
        self._model = None
        self._load_error: str | None = None
        self._device: str = "cpu"

    def build(self, session_id: str, segments: list[TranscriptSegment]) -> SoapResponse:
        if settings.use_huggingface_models:
            tokenizer, model = self._ensure_model()
            if tokenizer is not None and model is not None:
                generated = self._generate_with_model(session_id, segments, tokenizer, model)
                if generated is not None:
                    return generated

        return self._fallback_summary(session_id, segments)

    def _generate_with_model(self, session_id, segments, tokenizer, model):
        conversation = "\n".join(
            f"[{segment.speaker}] original={segment.source_text} | traducao={segment.translation_text}"
            for segment in segments
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a clinical documentation assistant for Portuguese hospitals. "
                    "Generate a SOAP draft in European Portuguese. "
                    "Use neutral clinical language. Return only valid JSON with the keys "
                    "subjective, objective, assessment, and plan."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Cria um rascunho SOAP em portugues europeu, com base nesta conversa clinica. "
                    "Mantem apenas informacao clinicamente suportada pela conversa.\n\n"
                    f"{conversation}"
                ),
            },
        ]

        try:
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = tokenizer(prompt, return_tensors="pt")
            if self._device != "cpu":
                inputs = {name: tensor.to(self._device) for name, tensor in inputs.items()}

            output = model.generate(
                **inputs,
                max_new_tokens=settings.soap_max_new_tokens,
                do_sample=False,
            )
            prompt_length = inputs["input_ids"].shape[1]
            generated_text = tokenizer.decode(output[0][prompt_length:], skip_special_tokens=True)
            parsed = self._extract_json(generated_text)
            if parsed is None:
                return None

            return SoapResponse(
                session_id=session_id,
                subjective=parsed["subjective"].strip(),
                objective=parsed["objective"].strip(),
                assessment=parsed["assessment"].strip(),
                plan=parsed["plan"].strip(),
                generated_at="",
                review_required=True,
                retention_notice=(
                    "O audio nao e guardado. O transcript fica apenas em memoria volatil "
                    "durante a consulta ativa e e eliminado quando a sessao termina."
                ),
            )
        except Exception:  # pragma: no cover - hardware/runtime dependent
            return None

    def _ensure_model(self):
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model
        if AutoTokenizer is None or AutoModelForCausalLM is None:
            self._load_error = "A dependencia transformers nao esta instalada."
            return None, None

        runtime = get_runtime_config()
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.soap_model_id,
                token=runtime.token,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.soap_model_id,
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

    def _extract_json(self, generated_text: str):
        match = re.search(r"\{.*\}", generated_text, re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

        required = ("subjective", "objective", "assessment", "plan")
        if not all(isinstance(payload.get(key), str) and payload.get(key).strip() for key in required):
            return None
        return payload

    def _fallback_summary(self, session_id: str, segments: list[TranscriptSegment]) -> SoapResponse:
        patient_segments = [segment for segment in segments if segment.speaker == "patient"]
        clinician_segments = [segment for segment in segments if segment.speaker == "clinician"]

        subjective = (
            "Sintomas referidos pelo doente: "
            + " ".join(self._clinician_readable_text(segment) for segment in patient_segments[:4])
            if patient_segments
            else "Nao foram captadas declaracoes diretas do doente. Confirmar historia e sintomas manualmente."
        )

        objective = (
            "Observacoes clinicas captadas: "
            + " ".join(self._clinician_readable_text(segment) for segment in clinician_segments[:3])
            if clinician_segments
            else "Informacao objetiva limitada na sessao de traducao. Completar exame objetivo no sistema clinico."
        )

        return SoapResponse(
            session_id=session_id,
            subjective=subjective,
            objective=objective,
            assessment=(
                "Interpretacao clinica pendente de validacao pelo clinico responsavel e revisao das traducoes."
            ),
            plan=(
                "1. Rever os segmentos marcados como incertos. 2. Completar observacao clinica e registo hospitalar. "
                "3. Copiar este SOAP apenas apos revisao final."
            ),
            generated_at="",
            review_required=True,
            retention_notice=(
                "O audio nao e guardado. O transcript fica apenas em memoria volatil "
                "durante a consulta ativa e e eliminado quando a sessao termina."
            ),
        )

    def _clinician_readable_text(self, segment: TranscriptSegment) -> str:
        if segment.translation_language == "pt-PT" and segment.translation_text:
            return segment.translation_text
        return segment.translation_text or segment.source_text


soap_generation_service = SoapGenerationService()
