from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.database import session_maker
from app.schemas.session import StreamAuthMessage, StreamControlMessage
from app.services.auth import decode_access_token
from app.services.session import SessionService
from app.services.streaming import StreamingSession


router = APIRouter(prefix="/ws/sessions", tags=["stream"])


@router.websocket("/{session_id}/stream")
async def stream_session(websocket: WebSocket, session_id: str):
    await websocket.accept()
    stream: StreamingSession | None = None

    try:
        auth_message = StreamAuthMessage.model_validate_json(await websocket.receive_text())
        if auth_message.type != "auth":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        current_user = decode_access_token(auth_message.token)
        with session_maker() as db:
            session = SessionService(db).get_session(session_id)

        if not session or session.clinician_id != current_user["sub"] or session.status != "ACTIVE":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        stream = StreamingSession(
            websocket=websocket,
            session_id=session_id,
            speaker=auth_message.speaker,
            source_language=auth_message.source_language,
            translation_language=auth_message.translation_language,
            sample_rate=auth_message.sample_rate,
        )
        await stream.send_ready()

        while True:
            message = await websocket.receive()
            message_type = message.get("type")
            if message_type == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                await stream.ingest_audio(message["bytes"])
                continue

            if message.get("text") is not None:
                control = StreamControlMessage.model_validate_json(message["text"])
                if control.type == "stop":
                    await stream.stop()
                continue
    except (ValidationError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except WebSocketDisconnect:
        pass
    finally:
        if stream is not None:
            await stream.close()
