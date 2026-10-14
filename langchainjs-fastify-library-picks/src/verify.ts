/**
 * Reads the project back from Opik's REST API and checks what the README
 * claims: one thread per reader, readable first/last messages, llm spans
 * with tokens and non-null cost. Run it after `npm run demo`.
 */
import { PROJECT_NAME } from "./server.js";

const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/$/, "");
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
};
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

async function get<T>(route: string, params: Record<string, string>): Promise<T> {
  const url = `${base}/v1/private/${route}?${new URLSearchParams({ project_name: PROJECT_NAME, ...params })}`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`${route}: ${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

interface Row { [key: string]: any }

let failures = 0;
function check(label: string, ok: boolean, detail: string) {
  if (!ok) failures++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}: ${detail}`);
}

const text = (v: any): string => v?.input?.value ?? v?.output?.value ?? "";

const traces = (await get<{ content: Row[]; total: number }>("traces", { size: "100" })).content;
const threads = (await get<{ content: Row[] }>("traces/threads", { size: "100" })).content;
const spans = (await get<{ content: Row[] }>("spans", { size: "500" })).content;
const llm = spans.filter((s) => s.type === "llm");
const retrieval = spans.filter((s) => s.name === "search-catalog");

check("traces", traces.length > 0, `${traces.length} traces, all named ${[...new Set(traces.map((t) => t.name))].join(", ")}`);
check("threads", threads.length > 0, threads.map((t) => `${t.id} (${t.number_of_messages / 2} turns)`).join(", "));
check(
  "thread transcripts read as sentences",
  threads.every((t) => text(t.first_message).length > 10 && text(t.last_message).length > 10),
  threads.map((t) => `"${text(t.first_message).slice(0, 40)}..."`).join(" | "),
);
check("llm spans carry tokens", llm.length > 0 && llm.every((s) => s.usage?.total_tokens > 0), `${llm.length} llm spans, model ${[...new Set(llm.map((s) => s.model))].join(", ")}`);
check(
  "llm spans carry cost",
  llm.length > 0 && llm.every((s) => s.total_estimated_cost > 0),
  `total $${llm.reduce((a, s) => a + (s.total_estimated_cost ?? 0), 0).toFixed(6)}`,
);
check(
  "catalog lookups are tool spans with documents",
  retrieval.length === traces.length && retrieval.every((s) => s.type === "tool" && Array.isArray(s.output?.documents)),
  `${retrieval.length} search-catalog spans (type ${[...new Set(retrieval.map((s) => s.type))].join(", ")})`,
);

console.log(`\nspan names: ${[...new Set(spans.map((s) => `${s.name}:${s.type}`))].join(", ")}`);
process.exit(failures ? 1 : 0);
