from typing import Literal

from pydantic import BaseModel, Field


SessionState = Literal["ACTIVE", "CLOSED"]
SpeakerRole = Literal["clinician", "patient"]
SourceMode = Literal["speech", "typed"]


class SessionCreateRequest(BaseModel):
    clinician_language: str = "pt-PT"
    patient_language: str = "en-GB"
    region: str = "pt-PT"
    shared_device: bool = True


class SessionStatusResponse(BaseModel):
    session_id: str
    status: SessionState
    clinician_language: str
    patient_language: str
    region: str
    shared_device: bool
    created_at: str
    ended_at: str | None = None
    transcript_retention: str = "ephemeral_memory_only"


class TranscriptSegment(BaseModel):
    segment_id: str
    speaker: SpeakerRole
    timestamp_ms: int
    created_at: str
    source_text: str
    source_language: str
    translation_text: str
    translation_language: str
    source_mode: SourceMode
    edited_by_clinician: bool = False
    is_uncertain: bool = False
    uncertainty_reasons: list[str] = Field(default_factory=list)
    translation_engine: str = "demo"


class TranscriptResponse(BaseModel):
    segments: list[TranscriptSegment]


class UtteranceCreateRequest(BaseModel):
    speaker: SpeakerRole
    source_text: str = Field(min_length=1, max_length=1200)
    source_language: str
    translation_language: str
    source_mode: SourceMode = "speech"


class UtteranceUpdateRequest(BaseModel):
    source_text: str = Field(min_length=1, max_length=1200)


class SoapResponse(BaseModel):
    session_id: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    generated_at: str
    review_required: bool = True
    retention_notice: str = (
        "Audio is never stored. Transcript content is kept only in volatile memory "
        "during the active consultation and purged when the session closes."
    )


class SessionCloseResponse(BaseModel):
    session: SessionStatusResponse
    soap: SoapResponse
