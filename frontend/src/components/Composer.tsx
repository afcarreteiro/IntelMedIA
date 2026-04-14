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
      <div className="speaker-toggle">
        <button
          type="button"
          className={speaker === 'clinician' ? 'is-active' : ''}
          onClick={() => onSpeakerChange('clinician')}
          disabled={disabled}
        >
          Clinician speaking
        </button>
        <button
          type="button"
          className={speaker === 'patient' ? 'is-active' : ''}
          onClick={() => onSpeakerChange('patient')}
          disabled={disabled}
        >
          Patient speaking
        </button>
      </div>

      <div className="composer-meta">
        <span>{sourceLanguageLabel}</span>
        <span>translated to</span>
        <span>{translationLanguageLabel}</span>
      </div>

      <textarea
        value={text}
        onChange={(event) => onTextChange(event.target.value)}
        placeholder="Type the spoken sentence here, or use dictation."
        disabled={disabled}
      />

      {interimText ? <div className="interim-pill">Listening: {interimText}</div> : null}

      <div className="button-row">
        {speechSupported ? (
          <button
            type="button"
            className={`button ${isListening ? 'button--danger' : 'button--secondary'}`}
            onClick={isListening ? onStopListening : onStartListening}
            disabled={disabled}
          >
            {isListening ? 'Stop Dictation' : 'Start Dictation'}
          </button>
        ) : null}

        <button type="button" className="button button--primary" onClick={onSend} disabled={disabled || isSubmitting || !text.trim()}>
          {isSubmitting ? 'Sending...' : 'Translate Utterance'}
        </button>
      </div>
    </section>
  );
}
