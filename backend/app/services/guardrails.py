import re
from typing import Iterable

from app.schemas.session import SoapResponse


class GuardrailService:
    NEGATION_PATTERNS = {
        "pt": {"nao", "não", "nunca", "sem"},
        "en": {"not", "no", "never", "without"},
        "fr": {"pas", "jamais", "sans"},
        "es": {"no", "nunca", "sin"},
    }

    def assess_translation_risk(self, source_text: str, translated_text: str) -> list[str]:
        reasons: list[str] = []

        if not translated_text.strip():
            reasons.append("No translated text was produced.")
            return reasons

        source_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", source_text))
        translated_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", translated_text))
        if source_numbers and source_numbers != translated_numbers:
            reasons.append("Numeric content may not have been preserved.")

        if self._contains_negation(source_text) and not self._contains_negation(translated_text):
            reasons.append("Negation may not have been preserved.")

        if len(source_text.split()) >= 12 and source_text.strip() == translated_text.strip():
            reasons.append("Translation matches source text and should be reviewed.")

        return reasons

    def validate_supported_language(self, language_code: str, supported: Iterable[str]) -> None:
        if language_code not in supported:
            raise ValueError(f"Unsupported language code: {language_code}")

    def validate_soap(self, soap: SoapResponse) -> SoapResponse:
        for field_name in ("subjective", "objective", "assessment", "plan"):
            value = getattr(soap, field_name)
            if not value.strip():
                raise ValueError(f"Missing required SOAP field: {field_name}")
        return soap

    def _contains_negation(self, text: str) -> bool:
        text_lower = text.lower()
        return any(pattern in text_lower for patterns in self.NEGATION_PATTERNS.values() for pattern in patterns)
