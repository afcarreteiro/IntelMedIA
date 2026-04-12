from fastapi import APIRouter, WebSocket

from app.services.orchestrator import Orchestrator

router = APIRouter(tags=["streaming"])
orchestrator = Orchestrator()


@router.websocket("/ws/{session_id}")
async def stream_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    payload = await websocket.receive_bytes()
    message_id = orchestrator.publish_audio(session_id=session_id, chunk=payload)
    await websocket.send_json({"type": "audio_queued", "message_id": message_id})
    await websocket.close()
