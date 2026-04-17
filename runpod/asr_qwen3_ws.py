import asyncio
import io
import os
import wave
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from qwen_asr import Qwen3ASRModel


MODEL_ID = os.getenv("ASR_MODEL_ID", "Qwen/Qwen3-ASR-1.7B")
API_KEY = os.getenv("ASR_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
GPU_MEMORY_UTILIZATION = float(os.getenv("ASR_GPU_MEMORY_UTILIZATION", "0.8"))
MAX_NEW_TOKENS = int(os.getenv("ASR_MAX_NEW_TOKENS", "64"))
UNFIXED_CHUNK_NUM = int(os.getenv("ASR_UNFIXED_CHUNK_NUM", "2"))
UNFIXED_TOKEN_NUM = int(os.getenv("ASR_UNFIXED_TOKEN_NUM", "5"))
CHUNK_SIZE_SEC = float(os.getenv("ASR_STREAM_CHUNK_SIZE_SEC", "2.0"))
TARGET_SAMPLE_RATE = 16000


class StartMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    api_key: str | None = None
    session_id: str | None = None
    source_language: str | None = None
    sample_rate: int = TARGET_SAMPLE_RATE
    audio_format: str = "wav"
    partial: bool = True


class ControlMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str


@dataclass
class SessionContext:
    session_id: str | None
    source_language: str | None
    partial: bool
    streaming_state: object
    last_text: str = ""


class QwenStreamingASR:
    def __init__(self) -> None:
        self._model: Qwen3ASRModel | None = None
        self._load_error: str | None = None
        self._lock = asyncio.Lock()

    def preload(self) -> tuple[bool, str | None]:
        if self._model is not None:
            return True, None

        try:
            self._model = Qwen3ASRModel.LLM(
                model=MODEL_ID,
                gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
                max_new_tokens=MAX_NEW_TOKENS,
            )
            self._load_error = None
            return True, None
        except Exception as exc:  # pragma: no cover - depends on runtime
            self._load_error = str(exc)
            return False, self._load_error

    def create_state(self):
        if self._model is None:
            raise RuntimeError(self._load_error or "ASR model is not loaded.")

        return self._model.init_streaming_state(
            unfixed_chunk_num=UNFIXED_CHUNK_NUM,
            unfixed_token_num=UNFIXED_TOKEN_NUM,
            chunk_size_sec=CHUNK_SIZE_SEC,
        )

    async def transcribe_chunk(self, samples: np.ndarray, state) -> tuple[str, str | None]:
        if self._model is None:
            raise RuntimeError(self._load_error or "ASR model is not loaded.")

        async with self._lock:
            await asyncio.to_thread(self._model.streaming_transcribe, samples, state)

        text = getattr(state, "text", "") or ""
        language = getattr(state, "language", None)
        return text.strip(), language

    async def finish(self, state) -> tuple[str, str | None]:
        if self._model is None:
            raise RuntimeError(self._load_error or "ASR model is not loaded.")

        async with self._lock:
            await asyncio.to_thread(self._model.finish_streaming_transcribe, state)

        text = getattr(state, "text", "") or ""
        language = getattr(state, "language", None)
        return text.strip(), language

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error


asr_service = QwenStreamingASR()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await asyncio.to_thread(asr_service.preload)
    yield


app = FastAPI(title="IntelMedIA RunPod ASR", version="0.1.0", lifespan=lifespan)


def _resample_to_16k(wav_array: np.ndarray, sample_rate: int) -> np.ndarray:
    if sample_rate == TARGET_SAMPLE_RATE:
        return wav_array.astype(np.float32, copy=False)

    wav_array = wav_array.astype(np.float32, copy=False)
    duration = wav_array.shape[0] / float(sample_rate)
    target_size = int(round(duration * TARGET_SAMPLE_RATE))
    if target_size <= 0:
        return np.zeros((0,), dtype=np.float32)

    old_axis = np.linspace(0.0, duration, num=wav_array.shape[0], endpoint=False)
    new_axis = np.linspace(0.0, duration, num=target_size, endpoint=False)
    return np.interp(new_axis, old_axis, wav_array).astype(np.float32)


def _decode_wav_chunk(payload: bytes) -> tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(payload), "rb") as wav_file:
        if wav_file.getnchannels() != 1:
            raise ValueError("Expected mono WAV audio.")
        if wav_file.getsampwidth() != 2:
            raise ValueError("Expected 16-bit PCM WAV audio.")
        if wav_file.getcomptype() != "NONE":
            raise ValueError("Expected uncompressed PCM WAV audio.")

        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())

    pcm16 = np.frombuffer(frames, dtype=np.int16)
    samples = pcm16.astype(np.float32) / 32768.0
    return samples, sample_rate


async def _send_json(websocket: WebSocket, payload: dict) -> None:
    await websocket.send_json(payload)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    ready, error = await asyncio.to_thread(asr_service.preload)
    if not ready:
        return JSONResponse(status_code=503, content={"status": "error", "detail": error})
    return {"status": "ready", "model": MODEL_ID}


@app.websocket("/ws/transcribe")
async def transcribe_ws(websocket: WebSocket):
    await websocket.accept()
    context: SessionContext | None = None

    try:
        ready, error = await asyncio.to_thread(asr_service.preload)
        if not ready:
            await _send_json(
                websocket,
                {"type": "error", "message": error or "ASR model failed to load."},
            )
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        raw_start = await websocket.receive_json()
        start = StartMessage.model_validate(raw_start)

        if start.type != "start":
            await _send_json(websocket, {"type": "error", "message": "Expected start message."})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if API_KEY and start.api_key != API_KEY:
            await _send_json(websocket, {"type": "error", "message": "Invalid API key."})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if start.audio_format.lower() != "wav":
            await _send_json(websocket, {"type": "error", "message": "Only WAV chunks are supported."})
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
            return

        context = SessionContext(
            session_id=start.session_id,
            source_language=start.source_language,
            partial=bool(start.partial),
            streaming_state=asr_service.create_state(),
        )

        await _send_json(
            websocket,
            {
                "type": "ready",
                "engine": MODEL_ID,
                "realtime_ready": True,
                "session_id": context.session_id,
            },
        )

        while True:
            message = await websocket.receive()
            message_type = message.get("type")
            if message_type == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                audio_bytes = message["bytes"]
                try:
                    samples, sample_rate = _decode_wav_chunk(audio_bytes)
                    samples = _resample_to_16k(samples, sample_rate)
                except Exception as exc:
                    await _send_json(websocket, {"type": "error", "message": f"Invalid WAV chunk: {exc}"})
                    continue

                if samples.size == 0:
                    await _send_json(websocket, {"type": "warning", "message": "empty_chunk"})
                    continue

                text, language = await asr_service.transcribe_chunk(samples, context.streaming_state)
                if context.partial and text and text != context.last_text:
                    context.last_text = text
                    await _send_json(
                        websocket,
                        {
                            "type": "partial",
                            "session_id": context.session_id,
                            "text": text,
                            "detected_language": language,
                            "is_final": False,
                        },
                    )
                continue

            if message.get("text") is None:
                continue

            control = ControlMessage.model_validate_json(message["text"])

            if control.type == "flush":
                text, language = await asr_service.finish(context.streaming_state)
                if text:
                    context.last_text = text
                    await _send_json(
                        websocket,
                        {
                            "type": "final",
                            "session_id": context.session_id,
                            "text": text,
                            "detected_language": language,
                            "is_final": True,
                        },
                    )
                context.streaming_state = asr_service.create_state()
                continue

            if control.type == "stop":
                text, language = await asr_service.finish(context.streaming_state)
                if text:
                    await _send_json(
                        websocket,
                        {
                            "type": "final",
                            "session_id": context.session_id,
                            "text": text,
                            "detected_language": language,
                            "is_final": True,
                        },
                    )
                await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
                return

            await _send_json(websocket, {"type": "warning", "message": f"unsupported_control:{control.type}"})

    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - runtime dependent
        if websocket.client_state.name != "DISCONNECTED":
            await _send_json(websocket, {"type": "error", "message": str(exc)})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
