// Reads the project back from Opik: traces, threads, llm-span cost, and the
// judge scores the online rule attaches. Polls until every trace is scored.
import { setTimeout as sleep } from "node:timers/promises";
import { loadEnv } from "./env";

loadEnv();
const { opikRequest } = await import("../lib/opik-api");
const { PROJECT_NAME } = await import("../lib/telemetry");
const { SCORE_NAME } = await import("../lib/rule");

interface Trace {
  id: string;
  name: string;
  thread_id?: string;
  feedback_scores?: { name: string; value: number; reason?: string }[];
}
interface Span {
  type: string;
  model?: string;
  total_estimated_cost?: number | null;
  usage?: Record<string, number>;
}

const q = encodeURIComponent(PROJECT_NAME);
const deadline = Date.now() + Number(process.env.VERIFY_TIMEOUT_S ?? 240) * 1000;
let traces: Trace[] = [];
// The judge runs server-side after the trace lands, so scores arrive a little later.
while (true) {
  // The judge's own runs are logged as "online_evaluation" traces in the same project; skip them.
  traces = (await opikRequest<{ content: Trace[] }>(`/v1/private/traces?project_name=${q}&size=100`)).content.filter(
    (t) => t.name !== "online_evaluation",
  );
  const scored = traces.filter((t) => t.feedback_scores?.some((s) => s.name === SCORE_NAME));
  console.log(`traces=${traces.length} scored=${scored.length}`);
  if (traces.length > 0 && scored.length === traces.length) break;
  if (Date.now() > deadline) break;
  await sleep(10_000);
}

const threads = new Set(traces.map((t) => t.thread_id).filter(Boolean));
console.log(`\nproject=${PROJECT_NAME} traces=${traces.length} threads=${threads.size}`);
for (const t of traces) {
  const spans = (await opikRequest<{ content: Span[] }>(`/v1/private/spans?project_name=${q}&trace_id=${t.id}&size=50`)).content;
  const llm = spans.find((s) => s.type === "llm");
  const score = t.feedback_scores?.find((s) => s.name === SCORE_NAME);
  console.log(
    `${t.id.slice(0, 8)} thread=${t.thread_id?.slice(0, 8)} spans=${spans.map((s) => s.type).join(",")} ` +
      `model=${llm?.model} tokens=${llm?.usage?.total_tokens} cost=${llm?.total_estimated_cost} ${SCORE_NAME}=${score?.value}`,
  );
}
const unscored = traces.filter((t) => !t.feedback_scores?.some((s) => s.name === SCORE_NAME));
if (traces.length === 0 || unscored.length > 0) {
  console.error(`\n${unscored.length} trace(s) have no ${SCORE_NAME} score yet.`);
  process.exit(1);
}
