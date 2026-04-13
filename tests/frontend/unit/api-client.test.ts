import { describe, expect, it } from "vitest";

import { createApiClient } from "../../../frontend/src/api/client";

describe("api client", () => {
  it("returns a stubbed login token", async () => {
    const response = await createApiClient().login("clinician", "intelmedia");

    expect(response.access_token).toBe("clinician-intelmedia-token");
    expect(response.token_type).toBe("bearer");
  });
});
