import { config } from "dotenv";
import { fileURLToPath } from "node:url";
import { VisitorDesk, type Turn } from "./bot.js";
import { DEMO_CONVERSATIONS } from "./conversations.js";
import { logFeedback, toThumbs, type TurnFeedback } from "./feedback.js";
import { loadFacts } from "./museum.js";
import { summarize } from "./summary.js";
import { opik } from "./tracing.js";

// Local .env first, then the repo-root one; neither overrides the shell.
config({ path: fileURLToPath(new URL("../.env", import.meta.url)) });
config({ path: fileURLToPath(new URL("../../.env", import.meta.url)) });

async function main(): Promise<void> {
  const facts = loadFacts();
  const feedback: TurnFeedback[] = [];

  for (const [conversationId, questions] of Object.entries(DEMO_CONVERSATIONS)) {
    console.log(`\n=== ${conversationId} ===`);
    const desk = new VisitorDesk(conversationId, facts);
    const turns: Turn[] = [];
    for (const question of questions) {
      console.log(`\nVisitor: ${question}`);
      const turn = await desk.answer(question);
      turns.push(turn);
      console.log(`Desk:    ${turn.reply}`);
      console.log(`         [${turn.promptTokens} prompt / ${turn.completionTokens} completion tokens]`);
    }
    const s = summarize(turns);
    console.log(`\n${conversationId}: prompt tokens per turn ${s.promptTokensPerTurn.join(" -> ")}`);

    // The wheelchair visitor liked the final answer about changing tickets.
    if (conversationId === "wheelchair-visit") {
      const last = turns[turns.length - 1];
      if (last) {
        feedback.push({
          traceId: last.traceId,
          value: toThumbs(true),
          reason: "Visitor clicked thumbs-up on the ticket-change answer.",
        });
      }
    }
  }

  await logFeedback(feedback);
  for (const f of feedback) console.log(`\nLogged visitor-satisfaction=${f.value} on trace ${f.traceId}`);

  // Traces are sent in batches in the background; flush before exit or the last ones are lost.
  await opik.flush();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
