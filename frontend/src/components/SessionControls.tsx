import { Session, StreamReadyEvent } from '../types';

interface SessionControlsProps {
  session: Session | null;
  canClose: boolean;
  isClosing: boolean;
  isDeleting: boolean;
  streamStatus: StreamReadyEvent | null;
  latencyLabel: string;
  onCloseSession: () => void;
  onDeleteSession: () => void;
}

export function SessionControls({
  session,
  canClose,
  isClosing,
  isDeleting,
  streamStatus,
  latencyLabel,
  onCloseSession,
  onDeleteSession,
}: SessionControlsProps) {
  if (!session) {
    return null;
  }

  const languagePair = `${session.clinician_language} -> ${session.patient_language}`;

  return (
    <section className="control-card">
      <div className="control-card__top">
        <div>
          <div className="eyebrow">CONSULTA</div>
          <h2>{languagePair}</h2>
          {streamStatus ? (
            <p>
              {streamStatus.asr_engine} {'->'} {streamStatus.mt_engine}
              {latencyLabel ? ` · ${latencyLabel}` : ''}
            </p>
          ) : null}
        </div>

        <div className="control-card__meta">
          <div>
            <span className="meta-label">Retencao</span>
            <strong>Volatil</strong>
          </div>
          <div>
            <span className="meta-label">Tempo real</span>
            <strong>{streamStatus?.realtime_ready ? 'Pronto' : 'Degradado'}</strong>
          </div>
        </div>
      </div>

      <div className="button-row">
        {session.status === 'ACTIVE' ? (
          <button type="button" className="button button--primary" onClick={onCloseSession} disabled={!canClose || isClosing}>
            {isClosing ? 'A gerar SOAP...' : 'Encerrar consulta'}
          </button>
        ) : null}
        <button type="button" className="button button--ghost" onClick={onDeleteSession} disabled={isDeleting}>
          {isDeleting ? 'A apagar...' : 'Apagar dados da sessao'}
        </button>
      </div>
    </section>
  );
}
