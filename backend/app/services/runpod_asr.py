import asyncio
import io
import json
import logging
import wave
from typing import Awaitable, Callable
from urllib.parse import urlsplit, urlunsplit

import httpx
import numpy as np
from websockets.asyncio.client import connect as connect_async
from websockets.sync.client import connect as connect_sync

from app.config import settings


logger = logging.getLogger(__name__)
RUNPOD_ENGINE_LABEL = "runpod:qwen3-asr"
GENERIC_ASR_UNAVAILABLE = "ASR service unavailable."
GENERIC_TRANSCRIPTION_FAILED = "The audio could not be transcribed."

PartialCallback = Callable[[dict], Awaitable[None]]
MessageCallback = Callable[[str], Awaitable[None]]


class RunPodASRClientError(RuntimeError):
    pass


def _normalize_ws_url(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme == "https":
        new_scheme = "wss"
    elif scheme == "http":
        new_scheme = "ws"
    elif scheme in {"ws", "wss"}:
        new_scheme = scheme
    else:
        raise ValueError(f"Unsupported RunPod ASR URL scheme: {parsed.scheme}")

    return urlunsplit((new_scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))


def _samples_to_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm16 = (clipped * 32767.0).astype(np.int16)
    return _pcm_bytes_to_wav_bytes(pcm16.tobytes(), sample_rate)


def _pcm_bytes_to_wav_bytes(pcm_bytes: bytes, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


def _parse_json_message(raw_message) -> dict:
    if isinstance(raw_message, bytes):
        raw_message = raw_message.decode("utf-8")
    return json.loads(raw_message)


class RunPodStreamingClient:
    def __init__(
        self,
        *,
        session_id: str,
        source_language: str,
        sample_rate: int,
        on_partial: PartialCallback,
        on_warning: MessageCallback,
        on_error: MessageCallback,
    ) -> None:
        self.session_id = session_id
        self.source_language = source_language
        self.sample_rate = sample_rate
        self.on_partial = on_partial
        self.on_warning = on_warning
        self.on_error = on_error
        self.engine_label = RUNPOD_ENGINE_LABEL
        self._connection = None
        self._receiver_task: asyncio.Task | None = None
        self._pending_final: asyncio.Future | None = None
        self._closed = False

    async def connect(self) -> None:
        websocket_url = _normalize_ws_url(settings.runpod_asr_ws_url)
        self._connection = await connect_async(
            websocket_url,
            open_timeout=settings.runpod_asr_connect_timeout_s,
            ping_interval=20,
            ping_timeout=20,
            max_size=None,
        ).__aenter__()

        await self._connection.send(
            json.dumps(
                {
                    "type": "start",
                    "api_key": settings.runpod_asr_api_key,
                    "session_id": self.session_id,
                    "source_language": self.source_language,
                    "sample_rate": self.sample_rate,
                    "audio_format": "wav",
                    "partial": True,
                }
            )
        )

        ready_payload = await asyncio.wait_for(
            self._recv_json(),
            timeout=settings.runpod_asr_partial_timeout_s,
        )
        if ready_payload.get("type") == "error":
            raise RunPodASRClientError(str(ready_payload.get("message") or GENERIC_ASR_UNAVAILABLE))
        if ready_payload.get("type") != "ready":
            raise RunPodASRClientError("Unexpected response from RunPod ASR service.")

        ready_engine = str(ready_payload.get("engine") or "").strip()
        if ready_engine:
            self.engine_label = f"runpod:{ready_engine}"

        self._receiver_task = asyncio.create_task(self._receive_loop())

    async def send_audio_pcm(self, pcm_bytes: bytes) -> None:
        if self._closed or self._connection is None or not pcm_bytes:
            return
        await self._connection.send(_pcm_bytes_to_wav_bytes(pcm_bytes, self.sample_rate))

    async def flush(self) -> dict:
        if self._closed or self._connection is None:
            raise RunPodASRClientError(GENERIC_ASR_UNAVAILABLE)

        loop = asyncio.get_running_loop()
        self._pending_final = loop.create_future()
        await self._connection.send(json.dumps({"type": "flush"}))
        return await asyncio.wait_for(
            self._pending_final,
            timeout=settings.runpod_asr_final_timeout_s,
        )

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        if self._receiver_task is not None:
            self._receiver_task.cancel()
            if self._receiver_task is not asyncio.current_task():
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass

        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def _recv_json(self) -> dict:
        if self._connection is None:
            raise RunPodASRClientError(GENERIC_ASR_UNAVAILABLE)
        raw_message = await self._connection.recv()
        return _parse_json_message(raw_message)

    async def _receive_loop(self) -> None:
        try:
            while not self._closed and self._connection is not None:
                payload = await self._recv_json()
                message_type = payload.get("type")
                if message_type == "partial":
                    await self.on_partial(payload)
                    continue
                if message_type == "final":
                    if self._pending_final is not None and not self._pending_final.done():
                        self._pending_final.set_result(payload)
                    continue
                if message_type == "warning":
                    await self.on_warning(str(payload.get("message") or "ASR warning."))
                    continue
                if message_type == "error":
                    detail = str(payload.get("message") or GENERIC_ASR_UNAVAILABLE)
                    if self._pending_final is not None and not self._pending_final.done():
                        self._pending_final.set_exception(RunPodASRClientError(detail))
                    await self.on_error(detail)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            detail = str(exc)
            if self._pending_final is not None and not self._pending_final.done():
                self._pending_final.set_exception(RunPodASRClientError(detail))
            await self.on_error(detail)
        finally:
            if self._connection is not None and not self._connection.closed:
                await self._connection.close()


class RunPodASRService:
    def preload(self) -> tuple[bool, str | None]:
        if not settings.runpod_asr_ws_url or not settings.runpod_asr_ready_url:
            return False, "RunPod ASR is not configured."
        if not settings.runpod_asr_api_key:
            return False, "RunPod ASR API key is not configured."

        try:
            response = httpx.get(
                settings.runpod_asr_ready_url,
                timeout=settings.runpod_asr_connect_timeout_s,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "ready":
                return False, GENERIC_ASR_UNAVAILABLE
            return True, None
        except Exception as exc:
            logger.warning("RunPod ASR readiness check failed: %s", exc)
            return False, GENERIC_ASR_UNAVAILABLE

    def transcribe_samples(
        self,
        *,
        samples: np.ndarray,
        sample_rate: int,
        language_code: str,
        session_id: str = "finalize",
    ) -> tuple[str, str | None, str, list[str]]:
        ready, _ = self.preload()
        if not ready:
            return "", None, RUNPOD_ENGINE_LABEL, [GENERIC_ASR_UNAVAILABLE]

        try:
            websocket_url = _normalize_ws_url(settings.runpod_asr_ws_url)
            with connect_sync(
                websocket_url,
                open_timeout=settings.runpod_asr_connect_timeout_s,
                ping_interval=20,
                ping_timeout=20,
                max_size=None,
            ) as websocket:
                websocket.send(
                    json.dumps(
                        {
                            "type": "start",
                            "api_key": settings.runpod_asr_api_key,
                            "session_id": session_id,
                            "source_language": language_code,
                            "sample_rate": sample_rate,
                            "audio_format": "wav",
                            "partial": False,
                        }
                    )
                )

                ready_payload = _parse_json_message(
                    websocket.recv(timeout=settings.runpod_asr_partial_timeout_s)
                )
                if ready_payload.get("type") == "error":
                    raise RunPodASRClientError(
                        str(ready_payload.get("message") or GENERIC_ASR_UNAVAILABLE)
                    )
                if ready_payload.get("type") != "ready":
                    raise RunPodASRClientError("Unexpected response from RunPod ASR service.")

                engine = str(ready_payload.get("engine") or "").strip()
                engine_label = f"runpod:{engine}" if engine else RUNPOD_ENGINE_LABEL

                websocket.send(_samples_to_wav_bytes(samples, sample_rate))
                websocket.send(json.dumps({"type": "flush"}))

                while True:
                    payload = _parse_json_message(
                        websocket.recv(timeout=settings.runpod_asr_final_timeout_s)
                    )
                    message_type = payload.get("type")
                    if message_type == "warning":
                        continue
                    if message_type == "error":
                        raise RunPodASRClientError(
                            str(payload.get("message") or GENERIC_ASR_UNAVAILABLE)
                        )
                    if message_type != "final":
                        continue

                    text = str(payload.get("text") or "").strip()
                    detected_language = payload.get("detected_language")
                    if not text:
                        return "", detected_language, engine_label, [GENERIC_TRANSCRIPTION_FAILED]
                    return text, detected_language, engine_label, []
        except Exception as exc:
            logger.warning("RunPod ASR transcription failed: %s", exc)
            return "", None, RUNPOD_ENGINE_LABEL, [GENERIC_ASR_UNAVAILABLE]

    async def create_stream(
        self,
        *,
        session_id: str,
        source_language: str,
        sample_rate: int,
        on_partial: PartialCallback,
        on_warning: MessageCallback,
        on_error: MessageCallback,
    ) -> RunPodStreamingClient:
        client = RunPodStreamingClient(
            session_id=session_id,
            source_language=source_language,
            sample_rate=sample_rate,
            on_partial=on_partial,
            on_warning=on_warning,
            on_error=on_error,
        )
        await client.connect()
        return client


runpod_asr_service = RunPodASRService()
