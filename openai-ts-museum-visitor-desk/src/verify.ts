import { opik, PROJECT_NAME } from "./tracing.js";

// Reads the project back from Opik: traces grouped by thread, llm spans with cost, feedback scores.
const traces = await opik.searchTraces({ projectName: PROJECT_NAME, maxResults: 100, truncate: false });
const spans = await opik.searchSpans({ projectName: PROJECT_NAME, maxResults: 200, truncate: false });

const threads = new Map<string, number>();
for (const t of traces) threads.set(t.threadId ?? "(none)", (threads.get(t.threadId ?? "(none)") ?? 0) + 1);

console.log(`project: ${PROJECT_NAME}`);
console.log(`traces: ${traces.length}`);
console.log(`threads: ${[...threads].map(([id, n]) => `${id} x${n}`).join(", ")}`);
console.log(`span types: ${[...new Set(spans.map((s) => s.type))].join(", ")}`);
const llm = spans.filter((s) => s.type === "llm");
console.log(`llm spans: ${llm.length}, with cost: ${llm.filter((s) => (s.totalEstimatedCost ?? 0) > 0).length}`);
for (const s of llm) {
  console.log(`  ${s.model} tokens=${JSON.stringify(s.usage)} cost=${s.totalEstimatedCost}`);
}
for (const t of traces) {
  for (const f of t.feedbackScores ?? []) console.log(`feedback on ${t.id}: ${f.name}=${f.value}`);
}
await opik.flush();
