import { describe, expect, it } from 'vitest';

import { formatSoapForClipboard, getUtteranceLanguages } from './consultation';

describe('consultation utilities', () => {
  it('maps clinician speech to patient language', () => {
    const result = getUtteranceLanguages(
      {
        session_id: '1',
        status: 'ACTIVE',
        clinician_language: 'pt-PT',
        patient_language: 'fr-FR',
        region: 'pt-PT',
        shared_device: true,
        created_at: new Date().toISOString(),
        transcript_retention: 'ephemeral_memory_only',
      },
      'clinician',
    );

    expect(result).toEqual({
      sourceLanguage: 'pt-PT',
      translationLanguage: 'fr-FR',
    });
  });

  it('formats a SOAP note for clipboard export', () => {
    const formatted = formatSoapForClipboard({
      session_id: '1',
      subjective: 'Patient reports fever.',
      objective: 'No vitals captured.',
      assessment: 'Review infection risk.',
      plan: 'Complete clinician review.',
      generated_at: new Date().toISOString(),
      review_required: true,
      retention_notice: 'Notice',
    });

    expect(formatted).toContain('Subjective: Patient reports fever.');
    expect(formatted).toContain('Plan: Complete clinician review.');
  });
});
