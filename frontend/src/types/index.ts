export type SessionState = 'ACTIVE' | 'CLOSED';
export type SpeakerRole = 'clinician' | 'patient';
export type SourceMode = 'speech' | 'typed';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  user_id: string;
  username: string;
  full_name: string;
}

export interface LanguageOption {
  code: string;
  label: string;
  region: string;
  speech_locale: string;
}

export interface CatalogResponse {
  region: string;
  transcript_retention: string;
  languages: LanguageOption[];
}

export interface Session {
  session_id: string;
  status: SessionState;
  clinician_language: string;
  patient_language: string;
  region: string;
  shared_device: boolean;
  created_at: string;
  ended_at?: string | null;
  transcript_retention: string;
}

export interface CreateSessionRequest {
  clinician_language: string;
  patient_language: string;
  region: string;
  shared_device: boolean;
}

export interface TranscriptSegment {
  segment_id: string;
  speaker: SpeakerRole;
  timestamp_ms: number;
  created_at: string;
  source_text: string;
  source_language: string;
  translation_text: string;
  translation_language: string;
  source_mode: SourceMode;
  edited_by_clinician: boolean;
  is_uncertain: boolean;
  uncertainty_reasons: string[];
  translation_engine: string;
}

export interface CreateSegmentRequest {
  speaker: SpeakerRole;
  source_text: string;
  source_language: string;
  translation_language: string;
  source_mode: SourceMode;
}

export interface AudioChunkRequest {
  chunk_id: string;
  sequence: number;
  started_at_ms: number;
  ended_at_ms: number;
  duration_ms: number;
  overlap_ms: number;
  sample_rate: number;
  payload_base64: string;
}

export interface AudioFinalizeRequest {
  speaker: SpeakerRole;
  source_language: string;
  translation_language: string;
}

export interface AudioFinalizeResponse {
  segment: TranscriptSegment;
  transcript_text: string;
  asr_engine: string;
}

export interface SoapSummary {
  session_id: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  generated_at: string;
  review_required: boolean;
  retention_notice: string;
}

export interface CloseSessionResponse {
  session: Session;
  soap: SoapSummary;
}
