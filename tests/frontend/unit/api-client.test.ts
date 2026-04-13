import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "../../../frontend/src/api/client";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses same-origin auth path by default", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token-123", token_type: "bearer" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await createApiClient().login("clinician", "intelmedia");

    expect(fetchMock).toHaveBeenCalledWith(
      "/auth/login",
      expect.objectContaining({ method: "POST" })
    );
  });
});
