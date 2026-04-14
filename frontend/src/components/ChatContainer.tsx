import { useEffect, useRef } from 'react';

import { Session, TranscriptSegment } from '../types';
import { ChatMessage } from './ChatMessage';

interface ChatContainerProps {
  session: Session | null;
  segments: TranscriptSegment[];
  onEditSegment: (segmentId: string, sourceText: string) => Promise<void>;
}

export function ChatContainer({ session, segments, onEditSegment }: ChatContainerProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [segments]);

  if (!session) {
    return (
      <section className="conversation-shell conversation-shell--empty">
        <div>
          <div className="eyebrow">Shared-screen consultation</div>
          <h2>Start a session to begin the live translation workflow.</h2>
          <p>
            Each card keeps the original sentence visible, but the translated output is the dominant text so
            the patient can read it quickly during the visit.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="conversation-shell">
      {segments.length === 0 ? (
        <div className="conversation-empty">
          <h2>The consultation is ready.</h2>
          <p>Use dictation or type the next utterance. The translated result will appear here with larger text.</p>
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
