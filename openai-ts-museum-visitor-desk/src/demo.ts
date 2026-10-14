import { config } from "dotenv";
import { fileURLToPath } from "node:url";
import { VisitorDesk } from "./bot.js";
import { opik } from "./tracing.js";
import { DEMO_CONVERSATIONS } from "./conversations.js";
import { loadFacts } from "./museum.js";

// Local .env first, then the repo-root one; neither overrides the shell.
config({ path: fileURLToPath(new URL("../.env", import.meta.url)) });
config({ path: fileURLToPath(new URL("../../.env", import.meta.url)) });

async function main(): Promise<void> {
  const facts = loadFacts();
  for (const [conversationId, turns] of Object.entries(DEMO_CONVERSATIONS)) {
    console.log(`\n=== ${conversationId} ===`);
    const desk = new VisitorDesk(conversationId, facts);
    for (const question of turns) {
      console.log(`\nVisitor: ${question}`);
      const turn = await desk.answer(question);
      console.log(`Desk:    ${turn.reply}`);
      console.log(`         [${turn.promptTokens} prompt / ${turn.completionTokens} completion tokens]`);
    }
  }
  // Traces are sent in batches in the background; flush before exit or the last ones are lost.
  await opik.flush();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
