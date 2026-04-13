import { useState } from "react";

import { createApiClient, type ApiClient } from "./api/client";
import { LoginForm } from "./components/LoginForm";
import { SessionControls } from "./components/SessionControls";
import { SoapPane } from "./components/SoapPane";
import { StatusBanner } from "./components/StatusBanner";
import { TranscriptPane } from "./components/TranscriptPane";
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
  const [working, setWorking] = useState(false);
  const [snapshot, setSnapshot] = useState(() => sessionStore.snapshot());
  const [submitLogin] = useState(() => createLoginSubmission({ client: apiClient, store: sessionStore }));
  const isAuthenticated = Boolean(snapshot.token);
  const hasSession = Boolean(snapshot.sessionId);
  const hasActiveSession = hasSession && snapshot.status === "ACTIVE";

  function syncSnapshot() {
    setSnapshot(sessionStore.snapshot());
  }

  async function handleSubmit(username: string, password: string) {
    if (submitting) {
      return;
    }

    setSubmitting(true);

    try {
      await submitLogin(username, password);
    } finally {
      setSubmitting(false);
      syncSnapshot();
    }
  }

  async function handleCreateSession() {
    if (working || !isAuthenticated || snapshot.status === "ACTIVE") {
      return;
    }

    setWorking(true);

    try {
      const session = await apiClient.createSession();
      sessionStore.startSession(session.session_id);
      sessionStore.replaceSegments([
        {
          segmentId: "draft-1",
          sourceText: "Draft transcript",
          translatedText: "",
          isFinal: false,
        },
      ]);
      syncSnapshot();
    } finally {
      setWorking(false);
    }
  }

  async function handleCloseSession() {
    if (working || !isAuthenticated || !hasActiveSession) {
      return;
    }

    setWorking(true);

    try {
      await apiClient.closeSession(snapshot.sessionId);
      sessionStore.closeSession();
      syncSnapshot();
    } finally {
      setWorking(false);
    }
  }

  async function handleDeleteSession() {
    if (working || !isAuthenticated || !hasSession) {
      return;
    }

    setWorking(true);

    try {
      await apiClient.deleteSession(snapshot.sessionId);
      sessionStore.deleteSession();
      syncSnapshot();
    } finally {
      setWorking(false);
    }
  }

  async function handleExportSoap() {
    if (working || !isAuthenticated || !hasSession) {
      return;
    }

    setWorking(true);

    try {
      const result = await apiClient.fetchSoap(snapshot.sessionId);
      sessionStore.setSoap(result.soap);
      syncSnapshot();
    } finally {
      setWorking(false);
    }
  }

  return (
    <main>
      <LoginForm onSubmit={handleSubmit} disabled={submitting || working} />
      <SessionControls
        canCreate={isAuthenticated && snapshot.status !== "ACTIVE"}
        canClose={isAuthenticated && hasActiveSession}
        canDelete={isAuthenticated && hasSession}
        disabled={working}
        onCreateSession={handleCreateSession}
        onCloseSession={handleCloseSession}
        onDeleteSession={handleDeleteSession}
      />
      <StatusBanner status={snapshot.status} />
      <TranscriptPane segments={snapshot.segments} />
      <SoapPane disabled={working || !isAuthenticated || !hasSession} soap={snapshot.soap} onExport={handleExportSoap} />
    </main>
  );
}
