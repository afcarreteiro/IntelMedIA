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
  void baseUrl;

  return {
    async login(username: string, password: string) {
      return Promise.resolve({ access_token: `${username}-${password}-token`, token_type: "bearer" });
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
