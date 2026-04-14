import {
  AudioChunkRequest,
  AudioFinalizeRequest,
  AudioFinalizeResponse,
  CatalogResponse,
  CloseSessionResponse,
  CreateSegmentRequest,
  CreateSessionRequest,
  LoginRequest,
  Session,
  SoapSummary,
  TokenResponse,
  TranscriptSegment,
  User,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers);

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const raw = await response.text();
    let message = raw;

    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      if (typeof parsed.detail === 'string' && parsed.detail.trim()) {
        message = parsed.detail;
      }
    } catch {
      if (!raw.trim()) {
        message = `HTTP ${response.status}`;
      }
    }

    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  login(credentials: LoginRequest) {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  me() {
    return request<User>('/auth/me');
  },

  getCatalog() {
    return request<CatalogResponse>('/catalog/languages');
  },

  getActiveSession() {
    return request<Session | null>('/sessions/active');
  },

  createSession(payload: CreateSessionRequest) {
    return request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getTranscript(sessionId: string) {
    return request<{ segments: TranscriptSegment[] }>(`/sessions/${sessionId}/transcript`);
  },

  createSegment(sessionId: string, payload: CreateSegmentRequest) {
    return request<TranscriptSegment>(`/sessions/${sessionId}/segments`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  uploadAudioChunk(sessionId: string, payload: AudioChunkRequest) {
    return request<{ chunk_id: string; accepted: boolean; processing_mode: string }>(`/sessions/${sessionId}/audio-chunks`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  finalizeAudioUtterance(sessionId: string, payload: AudioFinalizeRequest) {
    return request<AudioFinalizeResponse>(`/sessions/${sessionId}/audio-utterances/finalize`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  updateSegment(sessionId: string, segmentId: string, sourceText: string) {
    return request<TranscriptSegment>(`/sessions/${sessionId}/segments/${segmentId}`, {
      method: 'PATCH',
      body: JSON.stringify({ source_text: sourceText }),
    });
  },

  closeSession(sessionId: string) {
    return request<CloseSessionResponse>(`/sessions/${sessionId}/close`, {
      method: 'POST',
    });
  },

  getSoap(sessionId: string) {
    return request<SoapSummary>(`/sessions/${sessionId}/soap`);
  },

  deleteSession(sessionId: string) {
    return request<{ message: string }>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },
};

export function setToken(token: string) {
  localStorage.setItem('token', token);
}

export function getToken() {
  return localStorage.getItem('token');
}

export function clearToken() {
  localStorage.removeItem('token');
}
