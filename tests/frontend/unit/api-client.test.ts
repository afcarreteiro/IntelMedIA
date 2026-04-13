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

  it("creates, closes, and deletes sessions through backend endpoints", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "session-1", status: "IDLE" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: "session-1", status: "CLOSED" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ deleted_session_id: "session-1" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient();
    const created = await client.createSession();
    const closed = await client.closeSession("session-1");
    await client.deleteSession("session-1");

    expect(created).toEqual({ session_id: "session-1", status: "IDLE" });
    expect(closed).toEqual({ session_id: "session-1", status: "CLOSED" });
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/sessions", expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/sessions/session-1/close",
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/sessions/session-1",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("surfaces SOAP endpoint unavailability instead of faking success", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    vi.stubGlobal("fetch", fetchMock);

    await expect(createApiClient().fetchSoap("session-1")).rejects.toThrow("SOAP endpoint unavailable");
    expect(fetchMock).toHaveBeenCalledWith(
      "/sessions/session-1/soap",
      expect.objectContaining({ method: "GET" })
    );
  });
});
