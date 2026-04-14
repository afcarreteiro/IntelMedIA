import { User } from '../types';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  return (
    <header className="shell-header">
      <div>
        <div className="eyebrow">Portugal pilot</div>
        <h1>IntelMedIA</h1>
        <p>Clinically safe shared-screen translation for consultations.</p>
      </div>

      <div className="header-actions">
        <div className="privacy-pill">GDPR / no retained audio</div>
        {user ? (
          <div className="user-chip">
            <span>{user.full_name}</span>
            <button type="button" onClick={onLogout}>
              Sign out
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
