type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type SessionStatus = "IDLE" | "ACTIVE" | "CLOSED";

type SessionResponse = {
  session_id: string;
  status: SessionStatus;
};

type SoapResponse = {
  soap: string;
};

export type ApiClient = {
  login(username: string, password: string): Promise<LoginResponse>;
  createSession(): Promise<SessionResponse>;
  closeSession(sessionId: string): Promise<SessionResponse>;
  deleteSession(sessionId: string): Promise<void>;
  fetchSoap(sessionId: string): Promise<SoapResponse>;
};

export function createApiClient(baseUrl = ""): ApiClient {
  return {
    async login(username: string, password: string) {
      const response = await fetch(`${baseUrl}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      return response.json() as Promise<LoginResponse>;
    },
    async createSession() {
      const response = await fetch(`${baseUrl}/sessions`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Create session failed");
      }

      return response.json() as Promise<SessionResponse>;
    },
    async closeSession(sessionId: string) {
      const response = await fetch(`${baseUrl}/sessions/${sessionId}/close`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Close session failed");
      }

      return response.json() as Promise<SessionResponse>;
    },
    async deleteSession(sessionId: string) {
      const response = await fetch(`${baseUrl}/sessions/${sessionId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Delete session failed");
      }
    },
    async fetchSoap(sessionId: string) {
      const response = await fetch(`${baseUrl}/sessions/${sessionId}/soap`, {
        method: "GET",
      });

      if ([404, 405, 501].includes(response.status)) {
        throw new Error("SOAP endpoint unavailable");
      }

      if (!response.ok) {
        throw new Error("SOAP export failed");
      }

      return response.json() as Promise<SoapResponse>;
    },
  };
}
