import { Session } from '../types';

interface SessionControlsProps {
  session: Session | null;
  canClose: boolean;
  isClosing: boolean;
  isDeleting: boolean;
  onCloseSession: () => void;
  onDeleteSession: () => void;
}

export function SessionControls({
  session,
  canClose,
  isClosing,
  isDeleting,
  onCloseSession,
  onDeleteSession,
}: SessionControlsProps) {
  if (!session) {
    return null;
  }

  const languagePair = `${session.clinician_language} -> ${session.patient_language}`;

  return (
    <section className="control-card">
      <div>
        <div className="eyebrow">Consultation session</div>
        <h2>{languagePair}</h2>
        <p>Shared-device mode for a clinician-led consultation on one computer.</p>
      </div>

      <div className="control-grid">
        <div>
          <span className="meta-label">Status</span>
          <strong>{session.status}</strong>
        </div>
        <div>
          <span className="meta-label">Retention</span>
          <strong>volatile only</strong>
        </div>
      </div>

      <div className="button-row">
        {session.status === 'ACTIVE' ? (
          <button type="button" className="button button--primary" onClick={onCloseSession} disabled={!canClose || isClosing}>
            {isClosing ? 'Generating SOAP...' : 'End Consultation'}
          </button>
        ) : null}
        <button type="button" className="button button--ghost" onClick={onDeleteSession} disabled={isDeleting}>
          {isDeleting ? 'Deleting...' : 'Delete Session Data'}
        </button>
      </div>
    </section>
  );
}
