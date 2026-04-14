import { useEffect, useRef } from 'react';

import { Session, TranscriptSegment } from '../types';
import { ChatMessage } from './ChatMessage';
import { VolumeMeter } from './VolumeMeter';

interface ChatContainerProps {
  session: Session | null;
  segments: TranscriptSegment[];
  micLevel: number;
  micActive: boolean;
  onEditSegment: (segmentId: string, sourceText: string) => Promise<void>;
}

export function ChatContainer({ session, segments, micLevel, micActive, onEditSegment }: ChatContainerProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [segments]);

  if (!session) {
    return (
      <section className="conversation-shell conversation-shell--empty">
        <div>
          <div className="eyebrow">TRADUCAO EM CONSULTA</div>
          <h2>Inicie uma sessao para comecar.</h2>
          <p>A traducao aparece em destaque para facilitar a leitura do doente durante a consulta.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="conversation-shell">
      <div className="conversation-toolbar">
        <div>
          <div className="eyebrow">CONVERSA</div>
          <strong>{session.clinician_language} {'->'} {session.patient_language}</strong>
        </div>

        <VolumeMeter level={micLevel} active={micActive} />
      </div>

      {segments.length === 0 ? (
        <div className="conversation-empty">
          <h2>A consulta esta pronta.</h2>
          <p>Use o microfone ou escreva a proxima frase para apresentar a traducao no ecra.</p>
        </div>
      ) : (
        segments.map((segment) => (
          <ChatMessage key={segment.segment_id} segment={segment} session={session} onEdit={onEditSegment} />
        ))
      )}
      <div ref={bottomRef} />
    </section>
  );
}
