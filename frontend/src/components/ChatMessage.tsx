import { useState } from 'react';

import { Session, TranscriptSegment } from '../types';
import { formatClock } from '../utils/consultation';

interface ChatMessageProps {
  segment: TranscriptSegment;
  session: Session;
  onEdit: (segmentId: string, sourceText: string) => Promise<void>;
  live?: boolean;
}

function getLanguageChip(code: string) {
  return code.split('-')[0].toUpperCase();
}

function speakText(text: string, language: string) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = language;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

export function ChatMessage({ segment, session, onEdit, live = false }: ChatMessageProps) {
  const [draftText, setDraftText] = useState(segment.source_text);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const cardTone = segment.speaker === 'clinician' ? 'card--clinician' : 'card--patient';

  async function handleSave() {
    setIsSaving(true);
    await onEdit(segment.segment_id, draftText);
    setIsSaving(false);
    setIsEditing(false);
  }

  return (
    <article className={`message-card ${cardTone} ${live ? 'message-card--live' : ''}`}>
      <div className="message-topline">
        <span className="speaker-chip">{segment.speaker === 'clinician' ? 'Clinico' : 'Doente'}</span>
        <span>{live ? 'Ao vivo' : formatClock(segment.timestamp_ms)}</span>
      </div>

      <div className="message-wave">
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>

      <div className="message-body">
        <div className="message-source">
          <div className="message-language-chip">{getLanguageChip(segment.source_language)}</div>
          <div className="message-copy">
            <span className="message-label">Original</span>
            {isEditing ? (
              <textarea value={draftText} onChange={(event) => setDraftText(event.target.value)} />
            ) : (
              <p>{segment.source_text}</p>
            )}
          </div>
        </div>

        <div className="message-translation">
          <div className="message-language-chip">{getLanguageChip(segment.translation_language)}</div>
          <div className="message-copy">
            <span className="message-label">Traducao</span>
            <p className="translation-copy">{segment.translation_text}</p>
          </div>
          <button
            type="button"
            className="play-button"
            onClick={() => speakText(segment.translation_text, segment.translation_language)}
            aria-label="Reproduzir traducao"
          >
            Ouvir
          </button>
        </div>
      </div>

      {segment.is_uncertain ? (
        <div className="message-alert">
          <strong>Revisao necessaria.</strong>
          <span>{segment.uncertainty_reasons.join(' ')}</span>
        </div>
      ) : null}

      <div className="message-footer">
        <span>{segment.translation_engine.replace('_', ' ')}</span>
        {session.status === 'ACTIVE' && !live ? (
          isEditing ? (
            <div className="button-row">
              <button type="button" className="button button--ghost" onClick={() => setIsEditing(false)}>
                Cancelar
              </button>
              <button type="button" className="button button--secondary" onClick={handleSave} disabled={isSaving || !draftText.trim()}>
                {isSaving ? 'A guardar...' : 'Guardar'}
              </button>
            </div>
          ) : (
            <button type="button" className="link-button" onClick={() => setIsEditing(true)}>
              Editar original
            </button>
          )
        ) : null}
      </div>
    </article>
  );
}
