from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import MessageResponse
from app.schemas.session import (
    AudioChunkRequest,
    AudioChunkResponse,
    AudioFinalizeRequest,
    AudioFinalizeResponse,
    SessionCloseResponse,
    SessionCreateRequest,
    SessionStatusResponse,
    SoapResponse,
    TranscriptResponse,
    TranscriptSegment,
    UtteranceCreateRequest,
    UtteranceUpdateRequest,
)
from app.services.audio_store import audio_chunk_store
from app.services.asr_pipeline import asr_pipeline_service
from app.services.auth import get_current_user
from app.services.catalog import SUPPORTED_LANGUAGE_CODES
from app.services.guardrails import GuardrailService
from app.services.session import SessionService
from app.services.soap_generation import soap_generation_service
from app.services.soap_store import soap_store
from app.services.transcript_store import transcript_store
from app.services.translation import translation_service


router = APIRouter(prefix="/sessions", tags=["sessions"])


def _serialize_session(session) -> SessionStatusResponse:
    return SessionStatusResponse(
        session_id=session.id,
        status=session.status,
        clinician_language=session.clinician_language,
        patient_language=session.patient_language,
        region=session.region,
        shared_device=session.shared_device,
        created_at=session.created_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
    )


def _build_segment(
    *,
    session_id: str,
    speaker: str,
    source_text: str,
    source_language: str,
    translation_language: str,
    source_mode: str,
) -> TranscriptSegment:
    guardrail = GuardrailService()
    translated = translation_service.translate(
        source_text=source_text.strip(),
        source_language=source_language,
        target_language=translation_language,
    )
    combined_reasons = translated.uncertainty_reasons + guardrail.assess_translation_risk(
        source_text,
        translated.translated_text,
    )

    segment = transcript_store.create_segment(
        speaker=speaker,
        source_text=source_text.strip(),
        source_language=source_language,
        translation_text=translated.translated_text,
        translation_language=translation_language,
        source_mode=source_mode,
        edited_by_clinician=False,
        is_uncertain=bool(combined_reasons),
        uncertainty_reasons=combined_reasons,
        translation_engine=translated.engine,
    )
    return transcript_store.add_segment(session_id, segment)


@router.post("", response_model=SessionStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    guardrail = GuardrailService()

    for language_code in (request.clinician_language, request.patient_language):
        try:
            guardrail.validate_supported_language(language_code, SUPPORTED_LANGUAGE_CODES)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    existing = service.get_session_by_clinician(current_user["sub"])
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active session already exists",
        )

    session = service.create_session(current_user["sub"], request)
    return _serialize_session(session)


@router.get("/active", response_model=SessionStatusResponse | None)
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session_by_clinician(current_user["sub"])
    if not session:
        return None
    return _serialize_session(session)


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return _serialize_session(session)


@router.post("/{session_id}/segments", response_model=TranscriptSegment, status_code=status.HTTP_201_CREATED)
async def create_segment(
    session_id: str,
    request: UtteranceCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")

    guardrail = GuardrailService()
    for language_code in (request.source_language, request.translation_language):
        try:
            guardrail.validate_supported_language(language_code, SUPPORTED_LANGUAGE_CODES)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _build_segment(
        session_id=session_id,
        speaker=request.speaker,
        source_text=request.source_text,
        source_language=request.source_language,
        translation_language=request.translation_language,
        source_mode=request.source_mode,
    )


@router.post("/{session_id}/audio-chunks", response_model=AudioChunkResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_audio_chunk(
    session_id: str,
    request: AudioChunkRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")

    audio_chunk_store.add_chunk(
        session_id,
        {
            "chunk_id": request.chunk_id,
            "sequence": request.sequence,
            "started_at_ms": request.started_at_ms,
            "ended_at_ms": request.ended_at_ms,
            "duration_ms": request.duration_ms,
            "overlap_ms": request.overlap_ms,
            "sample_rate": request.sample_rate,
            "payload_base64": request.payload_base64,
        },
    )

    return AudioChunkResponse(chunk_id=request.chunk_id)


@router.post(
    "/{session_id}/audio-utterances/finalize",
    response_model=AudioFinalizeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def finalize_audio_utterance(
    session_id: str,
    request: AudioFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")

    guardrail = GuardrailService()
    for language_code in (request.source_language, request.translation_language):
        try:
            guardrail.validate_supported_language(language_code, SUPPORTED_LANGUAGE_CODES)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    chunks = audio_chunk_store.drain_session(session_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No buffered audio is available for transcription.",
        )

    transcription = asr_pipeline_service.transcribe_merged_chunks(chunks, request.source_language)
    transcript_text = transcription.text.strip()
    if transcription.engine == "asr_unavailable":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=" ".join(transcription.uncertainty_reasons) or "The ASR service is unavailable.",
        )
    if not transcript_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=" ".join(transcription.uncertainty_reasons) or "The audio could not be transcribed.",
        )

    segment = _build_segment(
        session_id=session_id,
        speaker=request.speaker,
        source_text=transcript_text,
        source_language=request.source_language,
        translation_language=request.translation_language,
        source_mode="speech",
    )
    segment.translation_engine = f"{transcription.engine} -> {segment.translation_engine}"

    if transcription.uncertainty_reasons:
        segment.is_uncertain = True
        segment.uncertainty_reasons = transcription.uncertainty_reasons + segment.uncertainty_reasons

    return AudioFinalizeResponse(
        segment=segment,
        transcript_text=transcript_text,
        asr_engine=transcription.engine,
    )


@router.patch("/{session_id}/segments/{segment_id}", response_model=TranscriptSegment)
async def update_segment(
    session_id: str,
    segment_id: str,
    request: UtteranceUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    existing_segments = transcript_store.get_session_segments(session_id)
    existing_segment = next((segment for segment in existing_segments if segment.segment_id == segment_id), None)
    if not existing_segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found")

    guardrail = GuardrailService()
    result = translation_service.translate(
        source_text=request.source_text.strip(),
        source_language=existing_segment.source_language,
        target_language=existing_segment.translation_language,
    )
    combined_reasons = result.uncertainty_reasons + guardrail.assess_translation_risk(
        request.source_text,
        result.translated_text,
    )

    updated_segment = transcript_store.update_segment(
        session_id=session_id,
        segment_id=segment_id,
        new_text=request.source_text.strip(),
        translation_text=result.translated_text,
        is_uncertain=bool(combined_reasons),
        uncertainty_reasons=combined_reasons,
        translation_engine=result.engine,
    )
    if not updated_segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found")
    return updated_segment


@router.post("/{session_id}/close", response_model=SessionCloseResponse)
async def close_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already closed")

    segments = transcript_store.get_session_segments(session_id)
    soap = soap_generation_service.build(session_id=session_id, segments=segments)
    soap = GuardrailService().validate_soap(soap)
    soap_store.set_soap(
        session_id,
        {
            "session_id": session_id,
            "subjective": soap.subjective,
            "objective": soap.objective,
            "assessment": soap.assessment,
            "plan": soap.plan,
            "review_required": soap.review_required,
            "retention_notice": soap.retention_notice,
        },
    )

    closed_session = service.close_session(session_id)
    audio_chunk_store.clear_session(session_id)
    transcript_store.clear_session(session_id)
    service.mark_transcript_purged(session_id)

    stored_soap = soap_store.get_soap(session_id)
    return SessionCloseResponse(
        session=_serialize_session(closed_session),
        soap=SoapResponse(
            session_id=session_id,
            subjective=stored_soap["subjective"],
            objective=stored_soap["objective"],
            assessment=stored_soap["assessment"],
            plan=stored_soap["plan"],
            generated_at=stored_soap["generated_at"],
            review_required=stored_soap.get("review_required", True),
            retention_notice=stored_soap.get("retention_notice", SoapResponse.model_fields["retention_notice"].default),
        ),
    )


@router.delete("/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    audio_chunk_store.clear_session(session_id)
    transcript_store.clear_session(session_id)
    soap_store.clear_session(session_id)
    service.delete_session(session_id)
    return MessageResponse(message="Session deleted")


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return TranscriptResponse(segments=transcript_store.get_session_segments(session_id))


@router.get("/{session_id}/soap", response_model=SoapResponse)
async def get_soap(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SessionService(db)
    session = service.get_session(session_id)

    if not session or session.clinician_id != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    soap = soap_store.get_soap(session_id)
    if not soap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOAP not generated yet")

    return SoapResponse(
        session_id=session_id,
        subjective=soap["subjective"],
        objective=soap["objective"],
        assessment=soap["assessment"],
        plan=soap["plan"],
        generated_at=soap["generated_at"],
        review_required=soap.get("review_required", True),
        retention_notice=soap.get("retention_notice", SoapResponse.model_fields["retention_notice"].default),
    )
