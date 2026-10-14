// Scripted demo: three customer messages through the booking assistant.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [
    fileURLToPath(new URL("../.env", import.meta.url)),
    fileURLToPath(new URL("../../.env", import.meta.url)),
  ],
  quiet: true,
});

// VoltAgent puts the system prompt in the messages array, which makes the AI SDK warn on every call.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

const { VoltAgent } = await import("@voltagent/core");
const { createBookingAgent } = await import("./agent.ts");
const { createObservability } = await import("./telemetry/setup.ts");

const agent = createBookingAgent();
// Passing observability to VoltAgent routes every agent run, llm call and tool call through the Opik exporter.
const observability = createObservability();
new VoltAgent({ agents: { agent }, observability });

export const REQUESTS = [
  "What would it cost to get my brakes sorted? They feel spongy.",
  "I'd like the basic tune-up for my green hybrid. Earliest slot please, and book it under Priya Nair.",
  "Can you check on booking BK-2201 for me?",
];

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Customer:  ${request}`);
  const result = await agent.generateText(request);
  console.log(`Assistant: ${result.text}`);
}
// Flush the batch processor so the last spans reach Opik before the process exits; otherwise they are lost.
await observability.shutdown();
console.log('\nDone. Open the "voltagent-bike-repair-booking" project in Opik to see the traces.');
process.exit(0);
