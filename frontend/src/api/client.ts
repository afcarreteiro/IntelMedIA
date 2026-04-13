type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type ApiClient = {
  login(username: string, password: string): Promise<LoginResponse>;
};

export function createApiClient(baseUrl = "http://localhost:8000"): ApiClient {
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
  };
}
