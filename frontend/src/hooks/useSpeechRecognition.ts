import { useCallback, useEffect, useRef, useState } from 'react';

type SpeechRecognitionCtor = new () => BrowserSpeechRecognition;

interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  }
}

export function useSpeechRecognition() {
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const callbackRef = useRef<((text: string) => void) | null>(null);
  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setIsSupported(Boolean(ctor));
  }, []);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setIsListening(false);
    setInterimTranscript('');
  }, []);

  const start = useCallback((language: string, onFinalTranscript: (text: string) => void) => {
    const ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!ctor) {
      setError('Speech recognition is not available in this browser.');
      return false;
    }

    callbackRef.current = onFinalTranscript;
    setError(null);
    setInterimTranscript('');

    const recognition = new ctor();
    recognition.lang = language;
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event) => {
      let interim = '';
      let finalText = '';

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result[0].transcript.trim();
        if (result.isFinal) {
          finalText += `${transcript} `;
        } else {
          interim += `${transcript} `;
        }
      }

      setInterimTranscript(interim.trim());

      if (finalText.trim()) {
        callbackRef.current?.(finalText.trim());
      }
    };

    recognition.onerror = (event) => {
      setError(event.error || 'Speech recognition failed.');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
    return true;
  }, []);

  useEffect(() => () => recognitionRef.current?.abort(), []);

  return {
    isSupported,
    isListening,
    interimTranscript,
    error,
    start,
    stop,
  };
}
