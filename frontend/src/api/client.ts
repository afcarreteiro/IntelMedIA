type LoginResponse = {
  access_token: string;
  token_type: string;
};

type CreateSessionResponse = {
  session_id: string;
  status: "ACTIVE";
};

type SoapResponse = {
  soap: string;
};

export type ApiClient = {
  login(username: string, password: string): Promise<LoginResponse>;
  createSession(): Promise<CreateSessionResponse>;
  closeSession(sessionId: string): Promise<void>;
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
      return Promise.resolve({ session_id: "session-local", status: "ACTIVE" });
    },
    async closeSession(sessionId: string) {
      void sessionId;
      return Promise.resolve();
    },
    async deleteSession(sessionId: string) {
      void sessionId;
      return Promise.resolve();
    },
    async fetchSoap(sessionId: string) {
      return Promise.resolve({ soap: `SOAP note for ${sessionId}` });
    },
  };
}
