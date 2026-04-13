import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "../../../frontend/src/api/client";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts login to same-origin auth path by default", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token-123", token_type: "bearer" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await createApiClient().login("clinician", "intelmedia");

    expect(fetchMock).toHaveBeenCalledWith(
      "/auth/login",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "clinician", password: "intelmedia" }),
      })
    );
    expect(response.access_token).toBe("token-123");
  });

  it("uses baseUrl when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token-abc", token_type: "bearer" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await createApiClient("http://localhost:8000").login("clinician", "intelmedia");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/login",
      expect.objectContaining({ method: "POST" })
    );
  });
});
