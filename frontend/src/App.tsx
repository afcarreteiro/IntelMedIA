import { FormEvent, useEffect, useMemo, useState } from 'react';

import { ChatContainer } from './components/ChatContainer';
import { Composer } from './components/Composer';
import { Header } from './components/Header';
import { SessionControls } from './components/SessionControls';
import { SessionSetup } from './components/SessionSetup';
import { SoapPanel } from './components/SoapPanel';
import { useStreamingAudioCapture } from './hooks/useStreamingAudioCapture';
import { api, clearToken, getToken, setToken } from './services/api';
import {
  LanguageOption,
  Session,
  SoapSummary,
  SpeakerRole,
  TranscriptSegment,
  User,
} from './types';
import { getUtteranceLanguages } from './utils/consultation';

function getLanguageLabel(languages: LanguageOption[], code: string) {
  return languages.find((language) => language.code === code)?.label ?? code;
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [loggingIn, setLoggingIn] = useState(false);
  const [startingSession, setStartingSession] = useState(false);
  const [submittingSegment, setSubmittingSegment] = useState(false);
  const [closingSession, setClosingSession] = useState(false);
  const [deletingSession, setDeletingSession] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [appError, setAppError] = useState('');

  const [username, setUsername] = useState('clinician');
  const [password, setPassword] = useState('intelmedia');

  const [user, setUser] = useState<User | null>(null);
  const [languages, setLanguages] = useState<LanguageOption[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [soapSummary, setSoapSummary] = useState<SoapSummary | null>(null);
  const [speaker, setSpeaker] = useState<SpeakerRole>('clinician');
  const [composerText, setComposerText] = useState('');
  const [clinicianLanguage, setClinicianLanguage] = useState('pt-PT');
  const [patientLanguage, setPatientLanguage] = useState('en-GB');

  const audioCapture = useStreamingAudioCapture({
    sessionId: session?.session_id ?? null,
    onChunk: async (chunk) => {
      if (!session) {
        return;
      }
      await api.uploadAudioChunk(session.session_id, chunk);
    },
  });

  useEffect(() => {
    void bootstrap();
  }, []);

  async function bootstrap() {
    setBooting(true);
    setAppError('');

    try {
      const catalog = await api.getCatalog();
      setLanguages(catalog.languages);

      if (!getToken()) {
        setBooting(false);
        return;
      }

      const me = await api.me();
      setUser(me);

      const activeSession = await api.getActiveSession();
      if (activeSession) {
        setSession(activeSession);
        setClinicianLanguage(activeSession.clinician_language);
        setPatientLanguage(activeSession.patient_language);
        const transcript = await api.getTranscript(activeSession.session_id);
        setSegments(transcript.segments);
      }
    } catch {
      clearToken();
      setUser(null);
      setSession(null);
      setSegments([]);
      setSoapSummary(null);
      setAppError('Nao foi possivel carregar o posto IntelMedIA.');
    } finally {
      setBooting(false);
    }
  }

  const utteranceLanguages = useMemo(
    () => (session ? getUtteranceLanguages(session, speaker) : null),
    [session, speaker],
  );

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setLoginError('');
    setLoggingIn(true);

    try {
      const response = await api.login({ username, password });
      setToken(response.access_token);
      const me = await api.me();
      setUser(me);
      await bootstrap();
    } catch (error) {
      setLoginError(getErrorMessage(error, 'Credenciais invalidas.'));
    } finally {
      setLoggingIn(false);
    }
  }

  function handleLogout() {
    audioCapture.stop();
    clearToken();
    setUser(null);
    setSession(null);
    setSegments([]);
    setSoapSummary(null);
  }

  async function handleStartSession() {
    setStartingSession(true);
    setAppError('');

    try {
      const created = await api.createSession({
        clinician_language: clinicianLanguage,
        patient_language: patientLanguage,
        region: 'pt-PT',
        shared_device: true,
      });

      setSession(created);
      setSegments([]);
      setSoapSummary(null);
      setSpeaker('clinician');
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel iniciar a sessao.'));
    } finally {
      setStartingSession(false);
    }
  }

  async function submitUtterance(text: string, sourceMode: 'speech' | 'typed') {
    if (!session || !utteranceLanguages || !text.trim()) {
      return;
    }

    setSubmittingSegment(true);
    setAppError('');

    try {
      const segment = await api.createSegment(session.session_id, {
        speaker,
        source_text: text.trim(),
        source_language: utteranceLanguages.sourceLanguage,
        translation_language: utteranceLanguages.translationLanguage,
        source_mode: sourceMode,
      });
      setSegments((current) => [...current, segment]);
      setComposerText('');
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel processar a traducao.'));
    } finally {
      setSubmittingSegment(false);
    }
  }

  async function handleEditSegment(segmentId: string, sourceText: string) {
    if (!session) {
      return;
    }

    try {
      const updated = await api.updateSegment(session.session_id, segmentId, sourceText);
      setSegments((current) => current.map((segment) => (segment.segment_id === segmentId ? updated : segment)));
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel guardar a edicao.'));
    }
  }

  async function handleStartListening() {
    if (!session || !utteranceLanguages || submittingSegment) {
      return;
    }

    const captureReady = await audioCapture.start();
    if (!captureReady) {
      setAppError('Nao foi possivel iniciar a captura de voz.');
    }
  }

  async function handleStopListening() {
    if (!audioCapture.isCapturing) {
      return true;
    }
    if (!session || !utteranceLanguages) {
      return false;
    }

    setSubmittingSegment(true);
    setAppError('');

    try {
      const uploadedChunks = await audioCapture.finish();
      if (uploadedChunks === 0) {
        setAppError('Nao foi captado audio suficiente para transcricao.');
        return false;
      }

      const response = await api.finalizeAudioUtterance(session.session_id, {
        speaker,
        source_language: utteranceLanguages.sourceLanguage,
        translation_language: utteranceLanguages.translationLanguage,
      });

      setSegments((current) => [...current, response.segment]);
      setComposerText(response.transcript_text);
      return true;
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel transcrever e traduzir o audio.'));
      return false;
    } finally {
      setSubmittingSegment(false);
    }
  }

  async function handleCloseSession() {
    if (!session) {
      return;
    }

    if (audioCapture.isCapturing) {
      const finalized = await handleStopListening();
      if (!finalized) {
        return;
      }
    }
    setClosingSession(true);

    try {
      const response = await api.closeSession(session.session_id);
      setSession(response.session);
      setSoapSummary(response.soap);
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel gerar o SOAP.'));
    } finally {
      setClosingSession(false);
    }
  }

  async function handleDeleteSession() {
    if (!session) {
      return;
    }

    audioCapture.stop();
    setDeletingSession(true);
    try {
      await api.deleteSession(session.session_id);
      setSession(null);
      setSegments([]);
      setSoapSummary(null);
      setSpeaker('clinician');
    } catch (error) {
      setAppError(getErrorMessage(error, 'Nao foi possivel apagar os dados da sessao.'));
    } finally {
      setDeletingSession(false);
    }
  }

  if (booting) {
    return <div className="loading-shell">A carregar IntelMedIA...</div>;
  }

  if (!user) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="eyebrow">INTELMEDIA MVP</div>
          <h1>Entrada do clinico</h1>
          <p>Use a conta de demonstracao para entrar no fluxo da consulta.</p>

          <form className="login-form" onSubmit={handleLogin}>
            <label>
              <span>Utilizador</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
            <label>
              <span>Palavra-passe</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            {loginError ? <div className="form-error">{loginError}</div> : null}
            <button type="submit" className="button button--primary" disabled={loggingIn}>
              {loggingIn ? 'A entrar...' : 'Entrar'}
            </button>
          </form>
        </section>
      </main>
    );
  }

  const sourceLanguageLabel = utteranceLanguages
    ? getLanguageLabel(languages, utteranceLanguages.sourceLanguage)
    : '';
  const translationLanguageLabel = utteranceLanguages
    ? getLanguageLabel(languages, utteranceLanguages.translationLanguage)
    : '';

  return (
    <main className="app-shell">
      <Header user={user} session={session} onLogout={handleLogout} />

      {appError ? <div className="app-error">{appError}</div> : null}
      {audioCapture.error ? <div className="app-error">{audioCapture.error}</div> : null}

      <div className="workspace-grid">
        <section className="workspace-main">
          {!session ? (
            <SessionSetup
              languages={languages}
              clinicianLanguage={clinicianLanguage}
              patientLanguage={patientLanguage}
              onClinicianLanguageChange={setClinicianLanguage}
              onPatientLanguageChange={setPatientLanguage}
              onStart={handleStartSession}
              isBusy={startingSession}
            />
          ) : (
            <>
              <SessionControls
                session={session}
                canClose={segments.length > 0}
                isClosing={closingSession}
                isDeleting={deletingSession}
                onCloseSession={handleCloseSession}
                onDeleteSession={handleDeleteSession}
              />

              <ChatContainer
                session={session}
                segments={segments}
                micLevel={audioCapture.level}
                micActive={audioCapture.isCapturing}
                onEditSegment={handleEditSegment}
              />

              {session.status === 'ACTIVE' ? (
                <Composer
                  speaker={speaker}
                  text={composerText}
                  interimText={audioCapture.isCapturing ? 'Captacao de voz ativa.' : ''}
                  sourceLanguageLabel={sourceLanguageLabel}
                  translationLanguageLabel={translationLanguageLabel}
                  speechSupported={audioCapture.isSupported}
                  isListening={audioCapture.isCapturing}
                  isSubmitting={submittingSegment}
                  disabled={closingSession || submittingSegment}
                  onSpeakerChange={setSpeaker}
                  onTextChange={setComposerText}
                  onSend={() => void submitUtterance(composerText, 'typed')}
                  onStartListening={() => void handleStartListening()}
                  onStopListening={() => void handleStopListening()}
                />
              ) : null}
            </>
          )}
        </section>

        <SoapPanel summary={soapSummary} />
      </div>
    </main>
  );
}
