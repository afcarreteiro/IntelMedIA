import type { TranscriptSegment } from "../types";

type SessionSnapshot = {
  token: string;
  sessionId: string;
  status: "IDLE" | "ACTIVE" | "CLOSED";
  segments: TranscriptSegment[];
  soap: string;
};

export type SessionStore = ReturnType<typeof createSessionStore>;

export function createSessionStore() {
  const snapshot: SessionSnapshot = { token: "", sessionId: "", status: "IDLE", segments: [], soap: "" };

  return {
    setToken(token: string) {
      snapshot.token = token;
    },
    startSession(sessionId: string, status: "IDLE" | "ACTIVE" | "CLOSED") {
      snapshot.sessionId = sessionId;
      snapshot.status = status;
      snapshot.soap = "";
      snapshot.segments = [];
    },
    closeSession(status: "IDLE" | "ACTIVE" | "CLOSED") {
      snapshot.status = status;
    },
    deleteSession() {
      snapshot.sessionId = "";
      snapshot.status = "IDLE";
      snapshot.segments = [];
      snapshot.soap = "";
    },
    addSegment(segment: TranscriptSegment) {
      snapshot.segments.push(segment);
    },
    replaceSegments(segments: TranscriptSegment[]) {
      snapshot.segments = [...segments];
    },
    setSoap(soap: string) {
      snapshot.soap = soap;
    },
    snapshot() {
      return structuredClone(snapshot);
    },
  };
}
