import { useState } from "react";

import { createApiClient, type ApiClient } from "./api/client";
import { LoginForm } from "./components/LoginForm";
import { createSessionStore, type SessionStore } from "./state/session-store";

const apiClient = createApiClient();
const sessionStore = createSessionStore();

export function createLoginSubmission({
  client,
  store,
}: {
  client: ApiClient;
  store: SessionStore;
}) {
  let inFlight: Promise<void> | null = null;

  return async (username: string, password: string) => {
    if (inFlight) {
      return inFlight;
    }

    const request = client
      .login(username, password)
      .then(({ access_token }) => {
        store.setToken(access_token);
      })
      .finally(() => {
        if (inFlight === request) {
          inFlight = null;
        }
      });

    inFlight = request;

    return request;
  };
}

export default function App() {
  const [submitting, setSubmitting] = useState(false);
  const [submitLogin] = useState(() => createLoginSubmission({ client: apiClient, store: sessionStore }));

  async function handleSubmit(username: string, password: string) {
    if (submitting) {
      return;
    }

    setSubmitting(true);

    try {
      await submitLogin(username, password);
    } finally {
      setSubmitting(false);
    }
  }

  return <LoginForm onSubmit={handleSubmit} disabled={submitting} />;
}
