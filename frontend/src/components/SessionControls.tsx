export function SessionControls({
  canCreate,
  canClose,
  canDelete,
  disabled,
  onCreateSession,
  onCloseSession,
  onDeleteSession,
}: {
  canCreate: boolean;
  canClose: boolean;
  canDelete: boolean;
  disabled?: boolean;
  onCreateSession: () => Promise<void>;
  onCloseSession: () => Promise<void>;
  onDeleteSession: () => Promise<void>;
}) {
  return (
    <div>
      <button type="button" onClick={() => void onCreateSession()} disabled={disabled || !canCreate}>
        Create session
      </button>
      <button type="button" onClick={() => void onCloseSession()} disabled={disabled || !canClose}>
        Close session
      </button>
      <button type="button" onClick={() => void onDeleteSession()} disabled={disabled || !canDelete}>
        Delete session
      </button>
    </div>
  );
}
