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
        <div className="eyebrow">Start the MVP workflow</div>
        <h2>Configure the consultation languages</h2>
        <p>
          The clinician keeps control on one shared device. IntelMedIA shows the translation larger than
          the original wording so the patient can read it easily.
        </p>
      </div>

      <div className="setup-grid">
        <label>
          <span>Clinician language</span>
          <select value={clinicianLanguage} onChange={(event) => onClinicianLanguageChange(event.target.value)}>
            {languages.map((language) => (
              <option key={language.code} value={language.code}>
                {language.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Patient language</span>
          <select value={patientLanguage} onChange={(event) => onPatientLanguageChange(event.target.value)}>
            {languages.map((language) => (
              <option key={language.code} value={language.code}>
                {language.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <ul className="setup-points">
        <li>Portugal-first configuration with GDPR-oriented handling.</li>
        <li>Transcript content stays in volatile memory during the active session.</li>
        <li>SOAP output is generated when the clinician closes the consultation.</li>
      </ul>

      <button type="button" className="button button--primary" onClick={onStart} disabled={isBusy}>
        {isBusy ? 'Starting...' : 'Start Consultation'}
      </button>
    </section>
  );
}
