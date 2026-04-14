import { Session, User } from '../types';

interface HeaderProps {
  user: User | null;
  session: Session | null;
  onLogout: () => void;
}

function getSessionLabel(status: Session['status']) {
  return status === 'ACTIVE' ? 'Sessao ativa' : 'Sessao encerrada';
}

export function Header({ user, session, onLogout }: HeaderProps) {
  const sessionTone = session?.status === 'ACTIVE' ? 'status-pill status-pill--live' : 'status-pill status-pill--closed';

  return (
    <header className="shell-header">
      <div>
        <div className="eyebrow">LANCAMENTO EM PORTUGAL</div>
        <h1>IntelMedIA</h1>
        <p>Traducao clinica em tempo real para consultas.</p>
      </div>

      <div className="header-actions">
        {session ? (
          <div className={sessionTone}>
            <span className="status-dot" />
            <span>{getSessionLabel(session.status)}</span>
          </div>
        ) : null}

        {user ? (
          <div className="user-chip">
            <span>{user.full_name}</span>
            <button type="button" onClick={onLogout}>
              Sair
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
