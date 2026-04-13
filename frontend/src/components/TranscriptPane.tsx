import type { TranscriptSegment } from "../types";

export function TranscriptPane({ segments }: { segments: TranscriptSegment[] }) {
  return (
    <section>
      <h2>Draft transcript</h2>
      <ul>
        {segments.map((segment) => (
          <li key={segment.segmentId}>{segment.sourceText}</li>
        ))}
      </ul>
    </section>
  );
}
