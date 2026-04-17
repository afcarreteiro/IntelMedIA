import { useCallback, useEffect, useRef, useState } from 'react';

import { getStreamingWebSocketUrl } from '../services/api';
import {
  SpeakerRole,
  StreamLatencyMetrics,
  StreamMetricsEvent,
  StreamPartialEvent,
  StreamReadyEvent,
  StreamSegmentFinalEvent,
  StreamWarningEvent,
  TranscriptSegment,
} from '../types';

interface StreamingAudioOptions {
  sessionId: string | null;
  token: string | null;
  onSegmentFinal: (segment: TranscriptSegment, metrics: StreamLatencyMetrics) => void;
  onTranscriptPartial: (text: string, engine: string, metrics: StreamLatencyMetrics) => void;
  onTranslationPartial: (text: string, engine: string, metrics: StreamLatencyMetrics) => void;
  onWarning: (message: string) => void;
  onMetrics: (metrics: StreamLatencyMetrics) => void;
  onReady: (payload: StreamReadyEvent) => void;
}

interface StartCaptureConfig {
  speaker: SpeakerRole;
  sourceLanguage: string;
  translationLanguage: string;
}

const SAMPLE_RATE = 16000;
const CHUNK_MS = 160;
const CHUNK_SAMPLES = Math.floor((SAMPLE_RATE * CHUNK_MS) / 1000);
const MIN_FLUSH_SAMPLES = Math.floor((SAMPLE_RATE * 450) / 1000);

function float32ToPcm16Buffer(samples: Float32Array) {
  const pcm16 = new Int16Array(samples.length);
  for (let index = 0; index < samples.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, samples[index]));
    pcm16[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return pcm16.buffer;
}

export function useStreamingAudioCapture({
  sessionId,
  token,
  onSegmentFinal,
  onTranscriptPartial,
  onTranslationPartial,
  onWarning,
  onMetrics,
  onReady,
}: StreamingAudioOptions) {
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isSupported] = useState(
    typeof window !== 'undefined'
      && typeof navigator !== 'undefined'
      && !!navigator.mediaDevices?.getUserMedia
      && !!window.AudioContext
      && 'AudioWorkletNode' in window,
  );

  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const frameRef = useRef<number | null>(null);
  const chunksSentRef = useRef(0);
  const finalEventWaiterRef = useRef<{ resolve: () => void; reject: (error: Error) => void } | null>(null);
  const readyWaiterRef = useRef<{ resolve: () => void; reject: (error: Error) => void } | null>(null);
  const closingExpectedRef = useRef(false);

  const stop = useCallback(() => {
    closingExpectedRef.current = true;
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }

    workletRef.current?.port.postMessage({ type: 'reset' });
    workletRef.current?.disconnect();
    sourceRef.current?.disconnect();
    analyserRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    socketRef.current?.close();
    contextRef.current?.close();

    workletRef.current = null;
    sourceRef.current = null;
    analyserRef.current = null;
    streamRef.current = null;
    socketRef.current = null;
    contextRef.current = null;
    chunksSentRef.current = 0;
    finalEventWaiterRef.current = null;
    readyWaiterRef.current = null;
    setLevel(0);
    setIsCapturing(false);
  }, []);

  const finish = useCallback(async () => {
    if (!isCapturing) {
      return false;
    }

    workletRef.current?.port.postMessage({ type: 'flush' });
    await new Promise((resolve) => window.setTimeout(resolve, 80));

    const socket = socketRef.current;
    const sentChunks = chunksSentRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN || sentChunks === 0) {
      stop();
      return false;
    }

    const finalized = new Promise<void>((resolve, reject) => {
      finalEventWaiterRef.current = { resolve, reject };
      window.setTimeout(() => {
        reject(new Error('A transcricao final demorou demasiado tempo a chegar.'));
      }, 20000);
    });
    socket.send(JSON.stringify({ type: 'stop' }));
    try {
      await finalized;
      stop();
      return true;
    } catch (error) {
      stop();
      throw error;
    }
  }, [isCapturing, stop]);

  const start = useCallback(async ({ speaker, sourceLanguage, translationLanguage }: StartCaptureConfig) => {
    if (isCapturing) {
      return true;
    }

    if (!sessionId || !token) {
      setError('Nao existe autenticacao ou sessao ativa para capturar audio.');
      return false;
    }
    if (!isSupported) {
      setError('Este dispositivo nao suporta captura de audio em tempo real no navegador.');
      return false;
    }

    try {
      setError(null);
      chunksSentRef.current = 0;
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const context = new AudioContext({ sampleRate: SAMPLE_RATE });
      await context.audioWorklet.addModule('/audio-capture-worklet.js');
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 128;
      const socket = new WebSocket(getStreamingWebSocketUrl(sessionId));
      socket.binaryType = 'arraybuffer';

      const readyPromise = new Promise<void>((resolve, reject) => {
        readyWaiterRef.current = { resolve, reject };
      });

      socket.onopen = () => {
        socket.send(JSON.stringify({
          type: 'auth',
          token,
          speaker,
          source_language: sourceLanguage,
          translation_language: translationLanguage,
          sample_rate: SAMPLE_RATE,
        }));
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data as string) as
          | StreamReadyEvent
          | StreamWarningEvent
          | StreamPartialEvent
          | StreamSegmentFinalEvent
          | StreamMetricsEvent;

        if (payload.type === 'ready') {
          onReady(payload);
          readyWaiterRef.current?.resolve();
          readyWaiterRef.current = null;
          return;
        }
        if (payload.type === 'warning') {
          onWarning(payload.message);
          return;
        }
        if (payload.type === 'metrics') {
          onMetrics(payload.metrics);
          return;
        }
        if (payload.type === 'transcript_partial') {
          onTranscriptPartial(payload.text, payload.engine, payload.metrics);
          return;
        }
        if (payload.type === 'translation_partial') {
          onTranslationPartial(payload.text, payload.engine, payload.metrics);
          return;
        }
        if (payload.type === 'segment_final') {
          onSegmentFinal(payload.segment, payload.metrics);
          finalEventWaiterRef.current?.resolve();
          finalEventWaiterRef.current = null;
        }
      };

      socket.onerror = () => {
        readyWaiterRef.current?.reject(new Error('Falhou a ligacao de streaming em tempo real.'));
        finalEventWaiterRef.current?.reject(new Error('Falhou a ligacao de streaming em tempo real.'));
        readyWaiterRef.current = null;
        finalEventWaiterRef.current = null;
        setError('Falhou a ligacao de streaming em tempo real.');
      };

      socket.onclose = () => {
        if (closingExpectedRef.current) {
          closingExpectedRef.current = false;
          return;
        }
        readyWaiterRef.current?.reject(new Error('A ligacao de streaming foi fechada.'));
        finalEventWaiterRef.current?.reject(new Error('A ligacao de streaming foi fechada.'));
        readyWaiterRef.current = null;
        finalEventWaiterRef.current = null;
        setError('A ligacao de streaming foi fechada.');
      };

      await readyPromise;

      const worklet = new AudioWorkletNode(context, 'audio-capture-processor', {
        numberOfInputs: 1,
        numberOfOutputs: 0,
        channelCount: 1,
        processorOptions: {
          chunkSize: CHUNK_SAMPLES,
          minFlushSize: MIN_FLUSH_SAMPLES,
        },
      });

      worklet.port.onmessage = (event) => {
        if (event.data?.type !== 'chunk') {
          return;
        }
        if (socket.readyState !== WebSocket.OPEN) {
          return;
        }
        const payload = event.data.payload as Float32Array;
        socket.send(float32ToPcm16Buffer(payload));
        chunksSentRef.current += 1;
      };

      source.connect(analyser);
      source.connect(worklet);

      streamRef.current = stream;
      contextRef.current = context;
      analyserRef.current = analyser;
      sourceRef.current = source;
      workletRef.current = worklet;
      socketRef.current = socket;
      closingExpectedRef.current = false;
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
  }, [
    isCapturing,
    isSupported,
    onMetrics,
    onReady,
    onSegmentFinal,
    onTranscriptPartial,
    onTranslationPartial,
    onWarning,
    sessionId,
    stop,
    token,
  ]);

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
    chunkMs: CHUNK_MS,
  };
}
