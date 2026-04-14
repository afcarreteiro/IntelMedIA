import { useCallback, useEffect, useRef, useState } from 'react';

import { AudioChunkRequest } from '../types';

interface StreamingAudioOptions {
  sessionId: string | null;
  onChunk: (chunk: AudioChunkRequest) => Promise<void> | void;
}

const SAMPLE_RATE = 16000;
const WINDOW_MS = 1400;
const OVERLAP_MS = 450;
const MIN_FINAL_CHUNK_MS = 450;
const STRIDE_MS = WINDOW_MS - OVERLAP_MS;
const WINDOW_SAMPLES = Math.floor((SAMPLE_RATE * WINDOW_MS) / 1000);
const OVERLAP_SAMPLES = Math.floor((SAMPLE_RATE * OVERLAP_MS) / 1000);
const STRIDE_SAMPLES = Math.floor((SAMPLE_RATE * STRIDE_MS) / 1000);
const MIN_FINAL_CHUNK_SAMPLES = Math.floor((SAMPLE_RATE * MIN_FINAL_CHUNK_MS) / 1000);

function pcm16ToBase64(samples: Int16Array) {
  const bytes = new Uint8Array(samples.buffer);
  let binary = '';
  for (let index = 0; index < bytes.byteLength; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return window.btoa(binary);
}

export function useStreamingAudioCapture({ sessionId, onChunk }: StreamingAudioOptions) {
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isSupported] = useState(
    typeof window !== 'undefined'
      && typeof navigator !== 'undefined'
      && !!navigator.mediaDevices?.getUserMedia
      && !!window.AudioContext,
  );

  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const frameRef = useRef<number | null>(null);
  const sampleBufferRef = useRef<Float32Array>(new Float32Array(0));
  const nextChunkStartMsRef = useRef<number>(0);
  const sequenceRef = useRef(0);
  const emittedChunksRef = useRef(0);
  const pendingUploadsRef = useRef(new Set<Promise<void>>());
  const uploadErrorRef = useRef<string | null>(null);

  const queueUpload = useCallback((chunk: AudioChunkRequest) => {
    const uploadPromise = Promise.resolve(onChunk(chunk))
      .catch(() => {
        uploadErrorRef.current = 'Falhou o envio de audio para transcricao.';
        setError(uploadErrorRef.current);
      })
      .finally(() => {
        pendingUploadsRef.current.delete(uploadPromise);
      });

    pendingUploadsRef.current.add(uploadPromise);
    emittedChunksRef.current += 1;
  }, [onChunk]);

  const emitChunk = useCallback((windowSamples: Float32Array, overlapMs: number) => {
    const pcm16 = new Int16Array(windowSamples.length);

    for (let index = 0; index < windowSamples.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, windowSamples[index]));
      pcm16[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }

    const startedAtMs = nextChunkStartMsRef.current;
    const durationMs = Math.round((windowSamples.length / SAMPLE_RATE) * 1000);
    const endedAtMs = startedAtMs + durationMs;

    queueUpload({
      chunk_id: crypto.randomUUID(),
      sequence: sequenceRef.current,
      started_at_ms: startedAtMs,
      ended_at_ms: endedAtMs,
      duration_ms: durationMs,
      overlap_ms: overlapMs,
      sample_rate: SAMPLE_RATE,
      payload_base64: pcm16ToBase64(pcm16),
    });

    sequenceRef.current += 1;
    nextChunkStartMsRef.current += STRIDE_MS;
  }, [queueUpload]);

  const flushTrailingChunk = useCallback(() => {
    const remainingSamples = sampleBufferRef.current;
    if (remainingSamples.length < MIN_FINAL_CHUNK_SAMPLES) {
      return;
    }

    emitChunk(remainingSamples, remainingSamples.length > OVERLAP_SAMPLES ? OVERLAP_MS : 0);
    sampleBufferRef.current = new Float32Array(0);
  }, [emitChunk]);

  const stop = useCallback(() => {
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    analyserRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    contextRef.current?.close();

    processorRef.current = null;
    sourceRef.current = null;
    analyserRef.current = null;
    streamRef.current = null;
    contextRef.current = null;
    sampleBufferRef.current = new Float32Array(0);
    sequenceRef.current = 0;
    emittedChunksRef.current = 0;
    setLevel(0);
    setIsCapturing(false);
  }, []);

  const finish = useCallback(async () => {
    flushTrailingChunk();
    const emittedChunks = emittedChunksRef.current;
    stop();

    if (pendingUploadsRef.current.size > 0) {
      await Promise.allSettled(Array.from(pendingUploadsRef.current));
    }

    if (uploadErrorRef.current) {
      const message = uploadErrorRef.current;
      uploadErrorRef.current = null;
      throw new Error(message);
    }

    pendingUploadsRef.current.clear();
    emittedChunksRef.current = 0;
    return emittedChunks;
  }, [flushTrailingChunk, stop]);

  const start = useCallback(async () => {
    if (isCapturing) {
      return true;
    }

    if (!sessionId) {
      setError('Nao existe uma sessao ativa para capturar audio.');
      return false;
    }
    if (!isSupported) {
      setError('Este dispositivo nao suporta captura de audio no navegador.');
      return false;
    }

    try {
      setError(null);
      uploadErrorRef.current = null;
      emittedChunksRef.current = 0;
      pendingUploadsRef.current.clear();
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const context = new AudioContext({ sampleRate: SAMPLE_RATE });
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 128;
      const processor = context.createScriptProcessor(2048, 1, 1);

      nextChunkStartMsRef.current = Date.now();
      sampleBufferRef.current = new Float32Array(0);

      processor.onaudioprocess = (event) => {
        const input = event.inputBuffer.getChannelData(0);
        const previous = sampleBufferRef.current;
        const combined = new Float32Array(previous.length + input.length);
        combined.set(previous, 0);
        combined.set(input, previous.length);
        sampleBufferRef.current = combined;

        while (sampleBufferRef.current.length >= WINDOW_SAMPLES) {
          const windowSamples = sampleBufferRef.current.slice(0, WINDOW_SAMPLES);
          emitChunk(windowSamples, OVERLAP_MS);
          sampleBufferRef.current = sampleBufferRef.current.slice(STRIDE_SAMPLES);
        }
      };

      source.connect(analyser);
      source.connect(processor);
      processor.connect(context.destination);

      streamRef.current = stream;
      contextRef.current = context;
      analyserRef.current = analyser;
      sourceRef.current = source;
      processorRef.current = processor;
      setIsCapturing(true);

      const loop = () => {
        const currentAnalyser = analyserRef.current;
        if (!currentAnalyser) {
          return;
        }

        const samples = new Uint8Array(currentAnalyser.frequencyBinCount);
        currentAnalyser.getByteFrequencyData(samples);
        const average = samples.reduce((sum, value) => sum + value, 0) / samples.length;
        setLevel(Math.min(1, average / 160));
        frameRef.current = requestAnimationFrame(loop);
      };

      loop();
      return true;
    } catch {
      setError('Permita o acesso ao microfone para usar entrada por voz.');
      stop();
      return false;
    }
  }, [emitChunk, isCapturing, isSupported, sessionId, stop]);

  useEffect(() => () => stop(), [stop]);

  return {
    level,
    error,
    isCapturing,
    isSupported,
    start,
    stop,
    finish,
    sampleRate: SAMPLE_RATE,
    windowMs: WINDOW_MS,
    overlapMs: OVERLAP_MS,
  };
}
