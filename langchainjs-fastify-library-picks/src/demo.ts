import { buildApp, flushOpik } from "./server.js";

const PORT = Number(process.env.PORT ?? 3162);

const CONVERSATIONS: Record<string, string[]> = {
  "reader-cozy-mystery": [
    "I want a cozy mystery set somewhere near the sea.",
    "Anything shorter? I only have a weekend.",
    "Is the first one dark, or more gentle?",
  ],
  "reader-space-optimist": [
    "I loved stories about robots and space. Something hopeful.",
    "Anything shorter than 300 pages?",
    "Great. Do you have anything funny for my dad too?",
  ],
  "reader-book-club": [
    "Our book club likes family stories with food in them.",
    "We meet in two weeks, so please keep it short.",
    "Thanks! Any travel memoir with humor for the next meeting?",
  ],
};

async function chat(sessionId: string, message: string): Promise<string> {
  const res = await fetch(`http://localhost:${PORT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!res.ok) throw new Error(`POST /chat failed: ${res.status} ${await res.text()}`);
  return ((await res.json()) as { reply: string }).reply;
}

async function main() {
  const app = buildApp();
  await app.listen({ port: PORT });
  for (const [sessionId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== ${sessionId} ===`);
    for (const message of turns) {
      console.log(`\nReader: ${message}`);
      console.log(`Picker: ${await chat(sessionId, message)}`);
    }
  }
  await flushOpik(); // send buffered traces before the process exits
  await app.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
