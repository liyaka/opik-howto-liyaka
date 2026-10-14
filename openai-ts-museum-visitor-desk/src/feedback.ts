import { opik } from "./tracing.js";

export interface TurnFeedback {
  traceId: string;
  value: number;
  reason: string;
}

export const FEEDBACK_NAME = "visitor-satisfaction";

export function toThumbs(up: boolean): number {
  return up ? 1 : 0;
}

export function buildFeedbackScores(items: TurnFeedback[]) {
  return items.map((f) => ({
    id: f.traceId,
    name: FEEDBACK_NAME,
    value: f.value,
    reason: f.reason,
  }));
}

// Attaches the scores to traces that already exist, after the run. They show up as a
// "visitor-satisfaction" column in the traces table, so you can sort or filter by it.
export async function logFeedback(items: TurnFeedback[]): Promise<void> {
  // Make sure the traces exist server-side before scoring them.
  await opik.flush();
  opik.logTracesFeedbackScores(buildFeedbackScores(items));
  await opik.flush();
}
