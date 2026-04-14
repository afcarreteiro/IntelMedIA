import { FormEvent, useEffect, useMemo, useState } from 'react';

import { ChatContainer } from './components/ChatContainer';
import { Composer } from './components/Composer';
import { Header } from './components/Header';
import { SessionControls } from './components/SessionControls';
import { SessionSetup } from './components/SessionSetup';
import { SoapPanel } from './components/SoapPanel';
import { VolumeMeter } from './components/VolumeMeter';
import { useAudioMeter } from './hooks/useAudioMeter';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';
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

  const speech = useSpeechRecognition();
  const audioMeter = useAudioMeter();

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!speech.isListening && audioMeter.isActive) {
      audioMeter.stop();
    }
  }, [audioMeter, speech.isListening]);

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
      setAppError('Unable to load the IntelMedIA workspace.');
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
    } catch {
      setLoginError('Invalid credentials.');
    } finally {
      setLoggingIn(false);
    }
  }

  function handleLogout() {
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
    } catch {
      setAppError('Unable to start the consultation session.');
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
    } catch {
      setAppError('The utterance could not be translated.');
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
    } catch {
      setAppError('The edited source text could not be saved.');
    }
  }

  async function handleStartListening() {
    if (!utteranceLanguages) {
      return;
    }

    const meterReady = await audioMeter.start();
    if (!meterReady) {
      return;
    }

    const speechReady = speech.start(utteranceLanguages.sourceLanguage, (finalText) => {
      setComposerText(finalText);
      void submitUtterance(finalText, 'speech');
    });

    if (!speechReady) {
      audioMeter.stop();
    }
  }

  function handleStopListening() {
    speech.stop();
    audioMeter.stop();
  }

  async function handleCloseSession() {
    if (!session) {
      return;
    }

    handleStopListening();
    setClosingSession(true);

    try {
      const response = await api.closeSession(session.session_id);
      setSession(response.session);
      setSoapSummary(response.soap);
    } catch {
      setAppError('The SOAP note could not be generated.');
    } finally {
      setClosingSession(false);
    }
  }

  async function handleDeleteSession() {
    if (!session) {
      return;
    }

    setDeletingSession(true);
    try {
      await api.deleteSession(session.session_id);
      setSession(null);
      setSegments([]);
      setSoapSummary(null);
      setSpeaker('clinician');
    } catch {
      setAppError('Session data could not be deleted.');
    } finally {
      setDeletingSession(false);
    }
  }

  if (booting) {
    return <div className="loading-shell">Loading IntelMedIA...</div>;
  }

  if (!user) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="eyebrow">IntelMedIA MVP</div>
          <h1>Clinician sign-in</h1>
          <p>Use the demo clinician account to enter the shared-device consultation workflow.</p>

          <form className="login-form" onSubmit={handleLogin}>
            <label>
              <span>Username</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} />
            </label>
            <label>
              <span>Password</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            {loginError ? <div className="form-error">{loginError}</div> : null}
            <button type="submit" className="button button--primary" disabled={loggingIn}>
              {loggingIn ? 'Signing in...' : 'Sign in'}
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
      <Header user={user} onLogout={handleLogout} />

      {appError ? <div className="app-error">{appError}</div> : null}
      {speech.error ? <div className="app-error">{speech.error}</div> : null}
      {audioMeter.error ? <div className="app-error">{audioMeter.error}</div> : null}

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

              <VolumeMeter level={audioMeter.level} active={speech.isListening} />

              <ChatContainer session={session} segments={segments} onEditSegment={handleEditSegment} />

              {session.status === 'ACTIVE' ? (
                <Composer
                  speaker={speaker}
                  text={composerText}
                  interimText={speech.interimTranscript}
                  sourceLanguageLabel={sourceLanguageLabel}
                  translationLanguageLabel={translationLanguageLabel}
                  speechSupported={speech.isSupported}
                  isListening={speech.isListening}
                  isSubmitting={submittingSegment}
                  disabled={closingSession}
                  onSpeakerChange={setSpeaker}
                  onTextChange={setComposerText}
                  onSend={() => void submitUtterance(composerText, 'typed')}
                  onStartListening={() => void handleStartListening()}
                  onStopListening={handleStopListening}
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
