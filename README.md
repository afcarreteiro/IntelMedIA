# IntelMedIA

IntelMedIA is a real-time medical translation web application designed for clinical consultations. Its purpose is to remove language barriers between clinicians and patients while preserving medical accuracy, privacy, and workflow efficiency.

The core experience is straightforward: the clinician speaks in their native language, IntelMedIA translates the conversation for the patient in the patient's native language, and the visit can end with an AI-generated SOAP summary that the clinician can review and transfer into the hospital system.

## MVP Definition

The initial MVP is a clinician-led web app used on the clinician's computer during the consultation. The patient also uses the same shared device or screen during the visit, rather than using a separate patient device.

The first launch is focused on Portugal. Language support should prioritize European languages, plus 5-6 of the most common African and Asian languages needed for patient communication in Portugal.

The clinical documentation output for the MVP should be a structured SOAP draft with these sections:

- Subjective
- Objective
- Assessment
- Plan

From a privacy and compliance perspective, the MVP should be treated as production-grade. Audio and transcripts should not be retained by default, and the product should be designed around GDPR-aligned handling of patient data.

## Who It Is For

IntelMedIA is intended for:

- Public hospitals
- Private hospitals
- Clinical teams serving multilingual patient populations

## Core Goals

- Enable real-time clinician-to-patient communication across languages
- Preserve clinical meaning and reduce translation ambiguity
- Support privacy-aware consultation workflows
- Reduce documentation burden with an AI-assisted SOAP summary
- Fit into hospital operations without slowing down care delivery

## Product Principles

- **Clinically safe:** the product should support care delivery without overstating certainty or replacing clinician judgment
- **Privacy-aware:** consultation data and summaries should be handled carefully and exposed only where necessary
- **Workflow-efficient:** the system should reduce friction during live consultations
- **Reviewable:** translations and summaries should support clinician confirmation when needed

## Conversation Layout Direction

The live consultation UI should follow the general direction of the provided reference layout:

- A clean two-party conversation view with clinician and patient messages visually separated
- Rounded speech cards with audio playback controls and waveform feedback
- Source-language text shown within each message
- Translated text displayed more prominently than the original text

Because IntelMedIA is focused on translation clarity during care delivery, the translated output should be the largest and most readable text element in each conversation card. The original spoken text can remain visible for review, but it should have lower visual emphasis than the translated result.

## Competitor-Informed Product Requirements

Based on comparable products in medical translation and interpreter access, IntelMedIA should address the following common customer frustrations:

- Make translated text large, high-contrast, and easy to read quickly for patients with poor vision, poor hearing, or noisy clinical surroundings.
- Keep audio routing reliable across speaker, handset, Bluetooth, and tablet hardware so live consultations do not fail because sound is sent to the wrong output.
- Design for unstable hospital Wi-Fi and degraded networks, with clear connection state feedback, graceful recovery, and no frozen or black-call states.
- Minimize login and setup friction so clinicians can start sessions fast without complicated account hierarchies, token confusion, or IT-heavy onboarding.
- Support a true real-time conversation flow instead of forcing users into rigid phrase-only workflows when a live exchange is needed.
- Preserve access to core functionality without deceptive paywalls or pricing surprises, especially for the most basic communication tasks.
- Provide specialty-aware medical language coverage so teams do not run into missing terms or missing workflows in areas such as radiology or emergency care.
- Fit hospital workflow better with clear summaries, export paths, and reporting that do not require awkward workarounds for billing, compliance, or documentation.
- Offer customization where it matters, including organization-specific workflows, readable print or export formats, and configurable operational settings.
- Build trust with predictable support and billing behavior so customers are not dealing with overcharges, cancellation disputes, or unclear ownership when problems happen.

## High-Level Architecture

- `frontend/`: React + TypeScript + Vite web client
- `backend/`: FastAPI service for sessions, auth, translation-related workflows, and SOAP summary support
- `docker-compose.yml`: local multi-service orchestration

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Additional frontend commands:

```bash
npm run build
npm test
npm run test:e2e
```

### Backend

```bash
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload
```

Backend tests:

```bash
pytest
```

### Full Stack

```bash
docker compose up --build
```

## Intended Consultation Flow

1. A clinician starts a consultation session.
2. The clinician speaks in their preferred language.
3. IntelMedIA processes and translates the speech for the patient.
4. The patient receives the content in their own language.
5. The session transcript can support creation of an AI-generated SOAP summary.
6. The clinician reviews the SOAP note before transferring it into the hospital system.

## Important Note

IntelMedIA should be presented as a clinician-support system, not as an autonomous medical decision-maker. Translation output and AI-generated SOAP summaries should remain reviewable within clinical workflow.
