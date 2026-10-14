// Reads the Opik project back over REST and asserts the lesson: every llm span has provider,
// model, token usage and a non-null total_estimated_cost, every trace has input and output.
// Run it after `npm run demo`; it exits 1 with the failing spans listed otherwise.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";
import { DEFAULT_PROJECT, opikOtlpConfig } from "./telemetry/setup.ts";

config({
  path: [
    fileURLToPath(new URL("../.env", import.meta.url)),
    fileURLToPath(new URL("../../.env", import.meta.url)),
  ],
  quiet: true,
});

type Row = Record<string, any>;

const base = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
const { headers } = opikOtlpConfig();
const project = headers.projectName ?? DEFAULT_PROJECT;

async function list(kind: "traces" | "spans"): Promise<Row[]> {
  // Opik's REST API reads the same workspace and project the OTLP exporter wrote to.
  const res = await fetch(`${base}/v1/private/${kind}?project_name=${encodeURIComponent(project)}&size=200`, {
    headers: {
      "Comet-Workspace": headers["Comet-Workspace"]!,
      ...(headers.Authorization ? { Authorization: headers.Authorization } : {}),
    },
  });
  if (!res.ok) throw new Error(`GET ${kind} -> ${res.status}`);
  return ((await res.json()) as { content: Row[] }).content;
}

const traces = await list("traces");
const spans = await list("spans");
const llm = spans.filter((s) => s.type === "llm");
const tools = spans.filter((s) => s.type === "tool");

console.log(`project ${project}: ${traces.length} traces, ${spans.length} spans (${llm.length} llm, ${tools.length} tool)`);
for (const s of llm) {
  console.log(
    `  llm   ${s.provider}/${s.model}  tokens=${JSON.stringify(s.usage)}  cost=$${s.total_estimated_cost ?? "null"}`,
  );
}
for (const s of tools) console.log(`  tool  ${s.name}  input=${JSON.stringify(s.input).slice(0, 70)}`);

const problems: string[] = [];
if (traces.length === 0) problems.push("no traces found");
if (llm.length === 0) problems.push("no llm spans: the gen_ai.* mapping did not reach Opik");
for (const s of llm) {
  if (!s.provider) problems.push(`llm span ${s.id}: provider missing, Opik cannot price it`);
  if (!s.usage?.total_tokens) problems.push(`llm span ${s.id}: token usage missing`);
  if (s.total_estimated_cost == null) problems.push(`llm span ${s.id}: total_estimated_cost is null (provider=${s.provider})`);
}
for (const t of traces) {
  if (!t.input || !t.output) problems.push(`trace ${t.id}: input or output column empty`);
}

if (problems.length > 0) {
  console.error("\nFAIL");
  for (const p of problems) console.error(`  - ${p}`);
  process.exit(1);
}
const total = traces.reduce((sum, t) => sum + (t.total_estimated_cost ?? 0), 0);
console.log(`\nOK: usage and cost present on every llm span, total estimated cost $${total.toFixed(6)}`);
