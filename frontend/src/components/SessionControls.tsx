export function SessionControls({
  hasSession,
  disabled,
  onCreateSession,
  onCloseSession,
  onDeleteSession,
}: {
  hasSession: boolean;
  disabled?: boolean;
  onCreateSession: () => Promise<void>;
  onCloseSession: () => Promise<void>;
  onDeleteSession: () => Promise<void>;
}) {
  return (
    <div>
      <button type="button" onClick={() => void onCreateSession()} disabled={disabled || hasSession}>
        Create session
      </button>
      <button type="button" onClick={() => void onCloseSession()} disabled={disabled || !hasSession}>
        Close session
      </button>
      <button type="button" onClick={() => void onDeleteSession()} disabled={disabled || !hasSession}>
        Delete session
      </button>
    </div>
  );
}
