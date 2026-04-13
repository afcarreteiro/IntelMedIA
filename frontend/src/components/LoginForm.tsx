import { useState } from "react";

export function LoginForm({
  onSubmit,
  disabled = false,
}: {
  onSubmit: (username: string, password: string) => Promise<void>;
  disabled?: boolean;
}) {
  const [username, setUsername] = useState("clinician");
  const [password, setPassword] = useState("intelmedia");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(username, password).catch(() => {
          return;
        });
      }}
    >
      <input value={username} onChange={(event) => setUsername(event.target.value)} disabled={disabled} />
      <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" disabled={disabled} />
      <button type="submit" disabled={disabled}>Sign in</button>
    </form>
  );
}
