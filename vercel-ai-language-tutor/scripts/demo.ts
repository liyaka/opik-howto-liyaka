// Scripted demo: registers the online-evaluation rule, starts the Next dev server,
// plays two multi-turn learner sessions against /api/chat, then shuts the server down.
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { setTimeout as sleep } from "node:timers/promises";
import { loadEnv } from "./env";
import { sessions } from "./sessions";

loadEnv();
const { ensureRule, RULE_NAME } = await import("../lib/rule");
const { PROJECT_NAME } = await import("../lib/telemetry");

const PORT = process.env.DEMO_PORT ?? "3181";
const BASE = `http://localhost:${PORT}`;

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// The rule must exist and be enabled before the first trace lands: Opik only
// scores traces that arrive after the rule is on.
const rule = await ensureRule(PROJECT_NAME);
console.log(`Rule ${RULE_NAME} ${rule.created ? "created" : "already present"} (${rule.id}), sampling 1.`);

console.log(`Starting Next.js dev server on port ${PORT}...`);
const next = spawn("npx", ["next", "dev", "-p", PORT], {
  env: { ...process.env },
  stdio: ["ignore", "pipe", "pipe"],
  detached: true,
});
next.stdout?.on("data", () => {});
next.stderr?.on("data", (d: Buffer) => {
  if (/error/i.test(d.toString())) process.stderr.write(d);
});

async function waitForServer(timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(BASE, { signal: AbortSignal.timeout(2000) })).ok) return;
    } catch {
      /* not up yet */
    }
    await sleep(500);
  }
  throw new Error("Dev server did not become ready in time");
}

// POSTs the whole history (what useChat does) and prints the streamed text deltas.
async function turn(id: string, lessonId: string, messages: unknown[]): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, lessonId, messages }),
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  let text = "";
  let buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) text += event.delta;
      } catch {
        /* keepalive */
      }
    }
  }
  console.log(text);
  return text;
}

const msg = (role: "user" | "assistant", text: string) => ({
  id: randomUUID(),
  role,
  parts: [{ type: "text", text }],
});

try {
  await waitForServer();
  for (const session of sessions) {
    const threadId = randomUUID();
    console.log(`\n=== ${session.title} (thread ${threadId.slice(0, 8)}) ===`);
    const history: unknown[] = [];
    for (const learner of session.turns) {
      console.log(`\nLearner: ${learner}\nProfe:`);
      history.push(msg("user", learner));
      history.push(msg("assistant", await turn(threadId, session.lessonId, history)));
    }
  }
  // The exporter batches spans; wait so the last turn is exported before shutdown.
  console.log("\nWaiting for traces to flush to Opik...");
  await sleep(10_000);
} finally {
  try {
    process.kill(-(next.pid as number), "SIGTERM");
  } catch {
    /* already gone */
  }
}
console.log(`Done. Run "npm run verify" to wait for the ${RULE_NAME} scores.`);
