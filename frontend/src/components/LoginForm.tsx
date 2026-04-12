import { useState } from "react";

export function LoginForm({ onSubmit }: { onSubmit: (username: string, password: string) => Promise<void> }) {
  const [username, setUsername] = useState("clinician");
  const [password, setPassword] = useState("intelmedia");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(username, password);
      }}
    >
      <input value={username} onChange={(event) => setUsername(event.target.value)} />
      <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
      <button type="submit">Sign in</button>
    </form>
  );
}
