import { useMemo, useState } from 'react';

import { SoapSummary } from '../types';
import { formatSoapForClipboard } from '../utils/consultation';

interface SoapPanelProps {
  summary: SoapSummary | null;
}

export function SoapPanel({ summary }: SoapPanelProps) {
  const [copied, setCopied] = useState(false);

  const clipboardText = useMemo(() => (summary ? formatSoapForClipboard(summary) : ''), [summary]);

  async function handleCopy() {
    if (!summary) {
      return;
    }
    await navigator.clipboard.writeText(clipboardText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  if (!summary) {
    return (
      <aside className="soap-panel soap-panel--placeholder">
        <div className="eyebrow">Structured SOAP</div>
        <h2>SOAP draft appears after the consultation ends.</h2>
        <p>
          IntelMedIA keeps transcripts in volatile memory during the visit, then produces a structured note for
          clinician review before the data is purged.
        </p>
      </aside>
    );
  }

  return (
    <aside className="soap-panel">
      <div className="soap-header">
        <div>
          <div className="eyebrow">Structured SOAP</div>
          <h2>Review before export</h2>
        </div>
        <button type="button" className="button button--secondary" onClick={handleCopy}>
          {copied ? 'Copied' : 'Copy SOAP'}
        </button>
      </div>

      <div className="soap-section">
        <h3>Subjective</h3>
        <p>{summary.subjective}</p>
      </div>
      <div className="soap-section">
        <h3>Objective</h3>
        <p>{summary.objective}</p>
      </div>
      <div className="soap-section">
        <h3>Assessment</h3>
        <p>{summary.assessment}</p>
      </div>
      <div className="soap-section">
        <h3>Plan</h3>
        <p>{summary.plan}</p>
      </div>

      <div className="soap-footer">
        <strong>Retention notice</strong>
        <p>{summary.retention_notice}</p>
      </div>
    </aside>
  );
}
