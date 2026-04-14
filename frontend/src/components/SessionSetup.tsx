import { LanguageOption } from '../types';

interface SessionSetupProps {
  languages: LanguageOption[];
  clinicianLanguage: string;
  patientLanguage: string;
  onClinicianLanguageChange: (value: string) => void;
  onPatientLanguageChange: (value: string) => void;
  onStart: () => void;
  isBusy: boolean;
}

export function SessionSetup({
  languages,
  clinicianLanguage,
  patientLanguage,
  onClinicianLanguageChange,
  onPatientLanguageChange,
  onStart,
  isBusy,
}: SessionSetupProps) {
  return (
    <section className="setup-card">
      <div>
        <div className="eyebrow">INICIAR CONSULTA</div>
        <h2>Escolha os idiomas</h2>
        <p>Configure apenas o essencial para comecar rapidamente.</p>
      </div>

      <div className="setup-grid">
        <label>
          <span>Idioma do clinico</span>
          <select value={clinicianLanguage} onChange={(event) => onClinicianLanguageChange(event.target.value)}>
            {languages.map((language) => (
              <option key={language.code} value={language.code}>
                {language.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Idioma do doente</span>
          <select value={patientLanguage} onChange={(event) => onPatientLanguageChange(event.target.value)}>
            {languages.map((language) => (
              <option key={language.code} value={language.code}>
                {language.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button type="button" className="button button--primary" onClick={onStart} disabled={isBusy}>
        {isBusy ? 'A iniciar...' : 'Comecar consulta'}
      </button>
    </section>
  );
}
