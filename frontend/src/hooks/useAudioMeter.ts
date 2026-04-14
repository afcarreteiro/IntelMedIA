import { useCallback, useEffect, useRef, useState } from 'react';

export function useAudioMeter() {
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const frameRef = useRef<number | null>(null);

  const stop = useCallback(() => {
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    contextRef.current?.close();
    contextRef.current = null;
    analyserRef.current = null;
    setLevel(0);
    setIsActive(false);
  }, []);

  const start = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 128;

      const source = context.createMediaStreamSource(stream);
      source.connect(analyser);

      streamRef.current = stream;
      contextRef.current = context;
      analyserRef.current = analyser;
      setIsActive(true);

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
      setError('Microphone permission is required for live dictation.');
      stop();
      return false;
    }
  }, [stop]);

  useEffect(() => () => stop(), [stop]);

  return {
    isActive,
    level,
    error,
    start,
    stop,
  };
}
