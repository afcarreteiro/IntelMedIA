from app.schemas.session import SoapResponse, TranscriptSegment


class SoapGenerationService:
    def build(self, session_id: str, segments: list[TranscriptSegment]) -> SoapResponse:
        patient_segments = [segment for segment in segments if segment.speaker == "patient"]
        clinician_segments = [segment for segment in segments if segment.speaker == "clinician"]

        return SoapResponse(
            session_id=session_id,
            subjective=self._render_subjective(patient_segments),
            objective=self._render_objective(clinician_segments),
            assessment=self._render_assessment(patient_segments, clinician_segments),
            plan=self._render_plan(),
            generated_at="",
        )

    def _render_subjective(self, patient_segments: list[TranscriptSegment]) -> str:
        if not patient_segments:
            return (
                "No direct patient statements were captured in the transcript. "
                "Confirm symptoms and history manually."
            )

        details = [self._clinician_readable_text(segment) for segment in patient_segments[:5]]
        return "Patient-reported concerns: " + " ".join(details)

    def _render_objective(self, clinician_segments: list[TranscriptSegment]) -> str:
        objective_candidates = [
            self._clinician_readable_text(segment)
            for segment in clinician_segments
            if self._looks_objective(segment.source_text)
        ]
        if objective_candidates:
            return "Captured clinician observations and actions: " + " ".join(objective_candidates[:4])
        return (
            "Limited objective data was captured during the translation session. "
            "Add examination findings, vitals, and measurements in the clinical record."
        )

    def _render_assessment(
        self,
        patient_segments: list[TranscriptSegment],
        clinician_segments: list[TranscriptSegment],
    ) -> str:
        combined_text = " ".join(
            self._clinician_readable_text(segment) for segment in patient_segments + clinician_segments
        ).lower()

        if "chest pain" in combined_text or "dor no peito" in combined_text:
            return (
                "Symptoms include chest pain. Urgent clinical assessment is required to "
                "exclude cardiopulmonary causes."
            )
        if "fever" in combined_text or "febre" in combined_text:
            return (
                "Febrile symptoms were reported. Correlate with examination findings, "
                "duration, exposure history, and infection workup as clinically indicated."
            )
        if "dizzy" in combined_text or "tonturas" in combined_text:
            return (
                "Dizziness was reported. Review hydration, orthostatic symptoms, medication "
                "effects, and neurologic red flags."
            )

        return (
            "Translation session completed. Clinical impression remains pending direct "
            "clinician assessment and confirmation of the translated content."
        )

    def _render_plan(self) -> str:
        return (
            "1. Confirm key history and any uncertain translation segments with the patient. "
            "2. Complete examination and document findings in the hospital system. "
            "3. Copy this structured note only after clinician review."
        )

    def _looks_objective(self, text: str) -> bool:
        lowered = text.lower()
        keywords = ("blood pressure", "tensao", "temperature", "fever", "exam", "measure", "oxygen")
        return any(keyword in lowered for keyword in keywords)

    def _clinician_readable_text(self, segment: TranscriptSegment) -> str:
        if segment.translation_language == "pt-PT" and segment.translation_text:
            return segment.translation_text
        return segment.translation_text or segment.source_text
