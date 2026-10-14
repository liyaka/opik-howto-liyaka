// Scripted demo runner: three complaints, three traces in the Opik project.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [
    fileURLToPath(new URL("../.env", import.meta.url)),
    fileURLToPath(new URL("../../.env", import.meta.url)),
  ],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Tracing must start before the agent module loads, and only after env vars are in place.
const { flushTracing, OPIK_PROJECT } = await import("./tracing.ts");
const { auditHousehold } = await import("./agent.ts");

const CASES: Array<[string, string]> = [
  ["HH-101", "Our electricity bill doubled in January and nothing in the house changed."],
  ["HH-102", "The heat pump keeps switching on and off every few minutes and the flat is never comfortable."],
  ["HH-103", "We use the house lightly, so why is the bill so high, even in the quiet winter months?"],
];

try {
  for (const [id, complaint] of CASES) {
    console.log(`\n=== ${id} ===\nComplaint: ${complaint}`);
    console.log(await auditHousehold(id, complaint));
  }
} finally {
  // Without flushing, the batch exporter can drop the final spans when the process exits.
  await flushTracing();
}
console.log(`\nDone. Open the "${OPIK_PROJECT}" project in Opik.`);
