// Runs three scripted customer requests through the Larkspur banking assistant.
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

const { mastra } = await import("./mastra.ts");

const REQUESTS = [
  "Hi, I'm Marisol. What's the balance on ACC-3001?",
  "What are the last four things that hit ACC-3001, and is any of it a subscription?",
  "I'm Desmond on ACC-4410 and my wallet was stolen at the train station. Please freeze my debit card right away.",
];

const agent = mastra.getAgent("bankingAgent");

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Customer: ${request}`);
  const result = await agent.generate(request, { maxSteps: 6 });
  console.log(`Agent:    ${result.text}`);
}

await mastra.shutdown();
console.log("\nDone.");
