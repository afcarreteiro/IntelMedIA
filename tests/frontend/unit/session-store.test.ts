import { describe, expect, it } from "vitest";
import { createSessionStore } from "../../../frontend/src/state/session-store";

describe("session store", () => {
  it("keeps transcript data in memory only", () => {
    const store = createSessionStore();

    store.setToken("token-123");
    store.addSegment({ segmentId: "seg-1", sourceText: "no pain", translatedText: "sem dor", isFinal: true });

    expect(store.snapshot().token).toBe("token-123");
    expect(window.localStorage.length).toBe(0);
  });
});
