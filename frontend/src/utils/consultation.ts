import { Session, SoapSummary, SpeakerRole } from '../types';

export function getUtteranceLanguages(session: Session, speaker: SpeakerRole) {
  if (speaker === 'clinician') {
    return {
      sourceLanguage: session.clinician_language,
      translationLanguage: session.patient_language,
    };
  }

  return {
    sourceLanguage: session.patient_language,
    translationLanguage: session.clinician_language,
  };
}

export function formatSoapForClipboard(summary: SoapSummary) {
  return [
    `Subjective: ${summary.subjective}`,
    `Objective: ${summary.objective}`,
    `Assessment: ${summary.assessment}`,
    `Plan: ${summary.plan}`,
  ].join('\n\n');
}

export function formatClock(isoOrMs: string | number) {
  const date = typeof isoOrMs === 'number' ? new Date(isoOrMs) : new Date(isoOrMs);
  return date.toLocaleTimeString('pt-PT', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
