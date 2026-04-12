from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.schemas.sessions import SessionState
from app.services.orchestrator import Orchestrator
from app.services.sessions import session_service

router = APIRouter(tags=["streaming"])
orchestrator = Orchestrator()


@router.websocket("/ws/{session_id}")
async def stream_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    session = session_service.get_session(session_id)
    if session is None or session.status is SessionState.CLOSED:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    while True:
        try:
            payload = await websocket.receive_bytes()
        except WebSocketDisconnect:
            return

        message_id = orchestrator.publish_audio(session_id=session_id, chunk=payload)
        await websocket.send_json({"type": "audio_queued", "message_id": message_id})
