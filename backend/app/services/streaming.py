import asyncio
import contextlib
import time
from dataclasses import dataclass, field

import numpy as np
from starlette.websockets import WebSocket

from app.config import settings
from app.schemas.session import (
    StreamLatencyMetrics,
    StreamMetricsEvent,
    StreamPartialEvent,
    StreamReadyEvent,
    StreamSegmentFinalEvent,
    StreamWarningEvent,
)
from app.services.asr_pipeline import asr_pipeline_service
from app.services.guardrails import GuardrailService
from app.services.metrics import (
    stream_connections_total,
    stream_latency_seconds,
    stream_messages_total,
)
from app.services.runpod_asr import (
    GENERIC_ASR_UNAVAILABLE,
    GENERIC_TRANSCRIPTION_FAILED,
    RunPodStreamingClient,
    runpod_asr_service,
)
from app.services.transcript_store import transcript_store
from app.services.translation import translation_service


def _ms_since(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 2)


@dataclass
class StreamTurnState:
    samples: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    speech_started_at: float | None = None
    last_voice_at: float | None = None
    last_partial_text: str = ""
    last_partial_translation: str = ""
    turn_index: int = 0


class StreamingSession:
    def __init__(
        self,
        *,
        websocket: WebSocket,
        session_id: str,
        speaker: str,
        source_language: str,
        translation_language: str,
        sample_rate: int,
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.speaker = speaker
        self.source_language = source_language
        self.translation_language = translation_language
        self.sample_rate = sample_rate
        self.guardrail = GuardrailService()
        self.turn = StreamTurnState()
        self._send_lock = asyncio.Lock()
        self._closed = False
        self._asr_stream: RunPodStreamingClient | None = None
        self._asr_failed = False

    async def send_ready(self):
        stream_connections_total.inc()
        asr_loaded, asr_error = await asyncio.to_thread(asr_pipeline_service.preload)
        mt_loaded, mt_error = await asyncio.to_thread(translation_service.preload)

        if asr_loaded:
            try:
                self._asr_stream = await runpod_asr_service.create_stream(
                    session_id=self.session_id,
                    source_language=self.source_language,
                    sample_rate=self.sample_rate,
                    on_partial=self._handle_asr_partial,
                    on_warning=self._handle_asr_warning,
                    on_error=self._handle_asr_error,
                )
            except Exception:
                asr_loaded = False
                asr_error = GENERIC_ASR_UNAVAILABLE

        if not asr_loaded:
            await self._send(
                StreamWarningEvent(
                    message=asr_error or GENERIC_ASR_UNAVAILABLE
                ).model_dump()
            )
        if not mt_loaded:
            await self._send(
                StreamWarningEvent(
                    message=mt_error or "O modelo MT nao ficou pronto para streaming."
                ).model_dump()
            )

        await self._send(
            StreamReadyEvent(
                asr_engine=self._asr_stream.engine_label if self._asr_stream else asr_pipeline_service.current_engine_label(),
                mt_engine=settings.nllb_model_id,
                realtime_ready=asr_loaded and mt_loaded,
            ).model_dump()
        )

    async def ingest_audio(self, payload: bytes):
        stream_messages_total.labels(type="audio").inc()
        if self._closed:
            return

        samples = np.frombuffer(payload, dtype=np.int16).astype(np.float32) / 32768.0
        if samples.size == 0:
            return

        self.turn.samples = np.concatenate((self.turn.samples, samples))

        now = time.perf_counter()
        frame_size = max(1, int(self.sample_rate * 0.02))
        for offset in range(0, len(samples), frame_size):
            frame = samples[offset: offset + frame_size]
            if frame.size == 0:
                continue

            if self._is_speech(frame):
                if self.turn.speech_started_at is None:
                    self.turn.speech_started_at = now
                    self.turn.turn_index += 1
                self.turn.last_voice_at = now

        if self._asr_stream is not None and not self._asr_failed:
            try:
                await self._asr_stream.send_audio_pcm(payload)
            except Exception as exc:
                await self._handle_asr_failure(str(exc))

        if self.turn.samples.size == 0:
            return

        silence_limit = settings.stream_endpoint_silence_ms / 1000
        max_turn = settings.stream_max_turn_ms / 1000
        if self.turn.last_voice_at is not None and now - self.turn.last_voice_at >= silence_limit:
            await self.finalize_turn()
        elif self.turn.speech_started_at is not None and now - self.turn.speech_started_at >= max_turn:
            await self.finalize_turn()

    async def stop(self):
        stream_messages_total.labels(type="stop").inc()
        await self.finalize_turn(force=True)

    async def close(self):
        self._closed = True
        if self._asr_stream is not None:
            with contextlib.suppress(Exception):
                await self._asr_stream.close()
            self._asr_stream = None

    async def finalize_turn(self, force: bool = False):
        if self.turn.samples.size == 0:
            return
        if not force and self.turn.speech_started_at is None:
            return

        turn_started_at = self.turn.speech_started_at or time.perf_counter()
        self.turn = StreamTurnState(turn_index=self.turn.turn_index)

        if self._asr_stream is None or self._asr_failed:
            await self._send(StreamWarningEvent(message=GENERIC_ASR_UNAVAILABLE).model_dump())
            return

        final_started = time.perf_counter()
        try:
            final_payload = await self._asr_stream.flush()
        except Exception as exc:
            await self._handle_asr_failure(str(exc))
            return

        transcript_text = str(final_payload.get("text") or "").strip()
        if not transcript_text:
            await self._send(StreamWarningEvent(message=GENERIC_TRANSCRIPTION_FAILED).model_dump())
            return

        translation_started = time.perf_counter()
        translated = await asyncio.to_thread(
            translation_service.translate,
            transcript_text,
            self.source_language,
            self.translation_language,
        )
        partial_mt_ms = _ms_since(translation_started)
        stream_latency_seconds.labels(stage="partial_mt").observe(partial_mt_ms / 1000)

        combined_reasons = translated.uncertainty_reasons + self.guardrail.assess_translation_risk(
            transcript_text,
            translated.translated_text,
        )
        segment = transcript_store.create_segment(
            speaker=self.speaker,
            source_text=transcript_text,
            source_language=self.source_language,
            translation_text=translated.translated_text,
            translation_language=self.translation_language,
            source_mode="speech",
            edited_by_clinician=False,
            is_uncertain=bool(combined_reasons),
            uncertainty_reasons=combined_reasons,
            translation_engine=f"{self._asr_stream.engine_label} -> {translated.engine}",
        )
        segment = transcript_store.add_segment(self.session_id, segment)

        endpoint_to_final_ms = _ms_since(final_started)
        final_turn_total_ms = _ms_since(turn_started_at)
        metrics = StreamLatencyMetrics(
            capture_to_server_ms=None,
            partial_asr_ms=None,
            partial_mt_ms=partial_mt_ms,
            endpoint_to_final_ms=endpoint_to_final_ms,
            final_turn_total_ms=final_turn_total_ms,
        )
        stream_latency_seconds.labels(stage="endpoint_to_final").observe(endpoint_to_final_ms / 1000)
        stream_latency_seconds.labels(stage="final_turn_total").observe(final_turn_total_ms / 1000)

        await self._send(StreamSegmentFinalEvent(segment=segment, metrics=metrics).model_dump())
        await self._send(StreamMetricsEvent(metrics=metrics).model_dump())

    async def _handle_asr_partial(self, payload: dict):
        text = str(payload.get("text") or "").strip()
        if not text or self._closed or self.turn.speech_started_at is None:
            return

        turn_index = self.turn.turn_index
        if text == self.turn.last_partial_text:
            return

        self.turn.last_partial_text = text
        await self._send(
            StreamPartialEvent(
                type="transcript_partial",
                text=text,
                speaker=self.speaker,
                source_language=self.source_language,
                translation_language=self.translation_language,
                engine=self._asr_stream.engine_label if self._asr_stream else asr_pipeline_service.current_engine_label(),
                metrics=StreamLatencyMetrics(),
            ).model_dump()
        )

        translation_started = time.perf_counter()
        translated = await asyncio.to_thread(
            translation_service.translate,
            text,
            self.source_language,
            self.translation_language,
        )
        partial_mt_ms = _ms_since(translation_started)
        stream_latency_seconds.labels(stage="partial_mt").observe(partial_mt_ms / 1000)
        translated_text = translated.translated_text.strip()
        if not translated_text or turn_index != self.turn.turn_index:
            return
        if translated_text == self.turn.last_partial_translation:
            return

        self.turn.last_partial_translation = translated_text
        metrics = StreamLatencyMetrics(partial_mt_ms=partial_mt_ms)
        await self._send(
            StreamPartialEvent(
                type="translation_partial",
                text=translated_text,
                speaker=self.speaker,
                source_language=self.source_language,
                translation_language=self.translation_language,
                engine=translated.engine,
                metrics=metrics,
            ).model_dump()
        )
        await self._send(StreamMetricsEvent(metrics=metrics).model_dump())

    async def _handle_asr_warning(self, _message: str):
        await self._handle_asr_failure(_message)

    async def _handle_asr_error(self, message: str):
        await self._handle_asr_failure(message)

    async def _handle_asr_failure(self, _detail: str):
        if self._asr_failed:
            return

        self._asr_failed = True
        if self._asr_stream is not None:
            stream = self._asr_stream
            self._asr_stream = None
            with contextlib.suppress(Exception):
                await stream.close()

        if not self._closed:
            await self._send(StreamWarningEvent(message=GENERIC_ASR_UNAVAILABLE).model_dump())

    async def _send(self, payload: dict):
        if self._closed:
            return
        stream_messages_total.labels(type=payload.get("type", "unknown")).inc()
        async with self._send_lock:
            await self.websocket.send_json(payload)

    def _is_speech(self, frame: np.ndarray) -> bool:
        if frame.size == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(frame))))
        return rms >= settings.stream_vad_threshold
