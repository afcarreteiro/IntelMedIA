import microphoneIcon from '../assets/microphone.svg';
import { SpeakerRole } from '../types';

interface ComposerProps {
  speaker: SpeakerRole;
  text: string;
  interimText: string;
  sourceLanguageLabel: string;
  translationLanguageLabel: string;
  speechSupported: boolean;
  isListening: boolean;
  isSubmitting: boolean;
  disabled: boolean;
  onSpeakerChange: (speaker: SpeakerRole) => void;
  onTextChange: (value: string) => void;
  onSend: () => void;
  onStartListening: () => void;
  onStopListening: () => void;
}

export function Composer({
  speaker,
  text,
  interimText,
  sourceLanguageLabel,
  translationLanguageLabel,
  speechSupported,
  isListening,
  isSubmitting,
  disabled,
  onSpeakerChange,
  onTextChange,
  onSend,
  onStartListening,
  onStopListening,
}: ComposerProps) {
  return (
    <section className="composer">
      <div className="composer-head">
        <div className="speaker-toggle">
          <button
            type="button"
            className={speaker === 'clinician' ? 'is-active' : ''}
            onClick={() => onSpeakerChange('clinician')}
            disabled={disabled || isListening}
          >
            Clinico
          </button>
          <button
            type="button"
            className={speaker === 'patient' ? 'is-active' : ''}
            onClick={() => onSpeakerChange('patient')}
            disabled={disabled || isListening}
          >
            Doente
          </button>
        </div>

        <div className="flow-pill">Preparado para conversa continua</div>
      </div>

      <div className="composer-meta">
        <span>{sourceLanguageLabel}</span>
        <span>{translationLanguageLabel}</span>
      </div>

      <div className="composer-input-row">
        <button
          type="button"
          className={`mic-button ${isListening ? 'mic-button--live' : ''}`}
          onClick={isListening ? onStopListening : onStartListening}
          disabled={disabled || !speechSupported}
          aria-label={isListening ? 'Parar captura de voz' : 'Iniciar captura de voz'}
          title={isListening ? 'Parar captura de voz' : 'Iniciar captura de voz'}
        >
          <img src={microphoneIcon} alt="" className="mic-button__image" />
          <span className="sr-only">
            {speechSupported
              ? (isListening ? 'Microfone ativo' : 'Microfone pronto')
              : 'Microfone indisponivel'}
          </span>
        </button>

        <textarea
          value={text}
          onChange={(event) => onTextChange(event.target.value)}
          placeholder="Escreva ou dite a frase da consulta."
          disabled={disabled}
        />
      </div>

      {interimText ? <div className="interim-pill">A ouvir: {interimText}</div> : null}

      <div className="button-row">
        <button
          type="button"
          className="button button--primary"
          onClick={onSend}
          disabled={disabled || isSubmitting || !text.trim()}
        >
          {isSubmitting ? 'A traduzir...' : 'Enviar traducao'}
        </button>
      </div>
    </section>
  );
}
