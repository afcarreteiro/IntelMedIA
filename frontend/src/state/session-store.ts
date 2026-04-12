import type { TranscriptSegment } from "../types";

type SessionSnapshot = {
  token: string;
  segments: TranscriptSegment[];
};

export function createSessionStore() {
  const snapshot: SessionSnapshot = { token: "", segments: [] };

  return {
    setToken(token: string) {
      snapshot.token = token;
    },
    addSegment(segment: TranscriptSegment) {
      snapshot.segments.push(segment);
    },
    snapshot() {
      return structuredClone(snapshot);
    },
  };
}
