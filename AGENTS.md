# AGENTS.md

## Project Overview
- **Project:** IntelMedIA, a real-time clinically safe medical translation web app for consultations.
- **Primary users:** Clinicians, care teams, and hospital administrators in public and private hospitals.
- **Core workflow:** A clinician speaks in their native language, the patient receives the translated output in their own language, and the consultation can end with an AI-generated SOAP summary for the clinical record.
- **Product priorities:** Medical accuracy, privacy, workflow efficiency, and clinically safe behavior under uncertainty.
- **Stack:** React + TypeScript + Vite frontend, FastAPI + Python backend, Docker Compose for local orchestration.

## MVP Scope
- **Primary runtime:** A clinician uses IntelMedIA on the clinician's computer during the consultation, with the patient also interacting with the same shared screen/device as needed.
- **Geographic focus:** Portugal only for the initial MVP.
- **Language scope:** European languages first, plus 5-6 of the most common African and Asian patient languages relevant to Portugal.
- **Clinical output:** Generate a structured SOAP draft with `Subjective`, `Objective`, `Assessment`, and `Plan` sections.
- **Privacy baseline:** Production-grade handling with no retained audio or transcripts by default.
- **Compliance baseline:** Features and data handling must align with GDPR expectations.

## Commands
- **Frontend install:** `cd frontend && npm install`
- **Frontend dev:** `cd frontend && npm run dev`
- **Frontend build:** `cd frontend && npm run build`
- **Frontend test:** `cd frontend && npm test`
- **Frontend e2e:** `cd frontend && npm run test:e2e`
- **Backend install:** `cd backend && pip install -e .[dev]`
- **Backend dev:** `cd backend && uvicorn app.main:app --reload`
- **Backend test:** `cd backend && pytest`
- **Full stack with Docker:** `docker compose up --build`

## Product Guardrails
- Preserve the clinical safety posture of the product in any feature or copy change.
- Prefer language such as `clinically safe`, `privacy-aware`, `human review`, and `workflow efficiency` where relevant.
- Do not imply autonomous diagnosis, treatment decisions, or fully unsupervised medical judgment.
- Surface uncertainty clearly when the system might need clinician confirmation.
- Protect privacy-sensitive data paths and avoid introducing unnecessary PHI exposure in logs, demos, or sample data.
- Assume audio and transcript retention are off by default unless explicitly justified and approved.
- Prefer Portugal-first workflows, language choices, and product framing for MVP decisions.

## Conversation UI Guidance
- Use the provided consultation mockup as the reference direction for the live translation conversation layout.
- Favor a two-sided chat layout with clear clinician and patient message separation.
- Each message card should support spoken input, waveform feedback, and translated output.
- The translated text must be visually larger and more prominent than the source-language text so it is easy to read during a live consultation.
- Keep the interface calm, sparse, and fast to scan, with translation readability prioritized over decorative UI.
- Preserve strong contrast, generous spacing, and large tap targets for audio playback and interaction controls.

## Do
- Read the existing code before making changes.
- Keep the clinician-patient translation workflow central in product decisions.
- Match existing code patterns, naming, and structure in `frontend/` and `backend/`.
- Keep changes scoped to the requested task.
- Handle failures explicitly, especially around translation accuracy, session state, auth, and summaries.
- Run the most relevant build/test commands after changes.
- Call out assumptions when requirements are ambiguous.

## Don't
- Add dependencies without a clear need.
- Hardcode secrets, tokens, credentials, or private clinical data.
- Introduce product claims that overstate safety, accuracy, compliance, or autonomy.
- Rewrite working areas of the app without cause.
- Make unrelated refactors during feature work.
- Push, deploy, or modify infrastructure beyond the task without permission.

## Testing
- Run relevant frontend or backend tests for every code change.
- Add tests for new backend logic and meaningful UI behavior when practical.
- Prefer targeted verification first, then broader validation if the change touches shared workflows.
- Never delete tests just to make the suite pass.

## Git
- Keep commits small and descriptive.
- Do not force-push.
- Do not overwrite user changes you did not make.

## Response Style
- Be clear, concise, and practical.
- Use plain English for product and engineering explanations.
- Keep recommendations grounded in the existing repo and the IntelMedIA clinical context.
