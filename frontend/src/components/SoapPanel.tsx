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
        <div className="eyebrow">SOAP ESTRUTURADO</div>
        <h2>O resumo aparece no fim da consulta.</h2>
        <p>Depois de encerrar a sessao, o clinico revê o SOAP antes de copiar para o sistema hospitalar.</p>
      </aside>
    );
  }

  return (
    <aside className="soap-panel">
      <div className="soap-header">
        <div>
          <div className="eyebrow">SOAP ESTRUTURADO</div>
          <h2>Rever antes de exportar</h2>
        </div>
        <button type="button" className="button button--secondary" onClick={handleCopy}>
          {copied ? 'Copiado' : 'Copiar SOAP'}
        </button>
      </div>

      <div className="soap-section">
        <h3>Subjetivo</h3>
        <p>{summary.subjective}</p>
      </div>
      <div className="soap-section">
        <h3>Objetivo</h3>
        <p>{summary.objective}</p>
      </div>
      <div className="soap-section">
        <h3>Avaliacao</h3>
        <p>{summary.assessment}</p>
      </div>
      <div className="soap-section">
        <h3>Plano</h3>
        <p>{summary.plan}</p>
      </div>

      <div className="soap-footer">
        <strong>Retencao</strong>
        <p>{summary.retention_notice}</p>
      </div>
    </aside>
  );
}
