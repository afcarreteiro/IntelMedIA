from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import MessageResponse
from app.schemas.session import (
    SessionCloseResponse,
    SessionCreateRequest,
    SessionStatusResponse,
    SoapResponse,
    TranscriptResponse,
    TranscriptSegment,
    UtteranceCreateRequest,
    UtteranceUpdateRequest,
)
from app.services.auth import get_current_user
from app.services.catalog import SUPPORTED_LANGUAGE_CODES
from app.services.guardrails import GuardrailService
from app.services.session import SessionService
from app.services.soap_generation import SoapGenerationService
from app.services.soap_store import soap_store
from app.services.transcript_store import transcript_store
from app.services.translation import TranslationService


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

    translation_service = TranslationService()
    guardrail = GuardrailService()
    result = translation_service.translate(
        source_text=request.source_text.strip(),
        source_language=request.source_language,
        target_language=request.translation_language,
    )
    combined_reasons = result.uncertainty_reasons + guardrail.assess_translation_risk(
        request.source_text,
        result.translated_text,
    )

    segment = transcript_store.create_segment(
        speaker=request.speaker,
        source_text=request.source_text.strip(),
        source_language=request.source_language,
        translation_text=result.translated_text,
        translation_language=request.translation_language,
        source_mode=request.source_mode,
        edited_by_clinician=False,
        is_uncertain=bool(combined_reasons),
        uncertainty_reasons=combined_reasons,
        translation_engine=result.engine,
    )
    return transcript_store.add_segment(session_id, segment)


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

    translation_service = TranslationService()
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
    soap = SoapGenerationService().build(session_id=session_id, segments=segments)
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
