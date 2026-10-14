import { config } from "dotenv";

config({ path: new URL("../../.env", import.meta.url).pathname });
config({ path: new URL("../.env", import.meta.url).pathname });

import { RULEBOOK, answerQuestion, createClient } from "./qa.js";
import { checkQuotes } from "./quotes.js";
import { QUESTIONS } from "./questions.js";

async function main(): Promise<void> {
  const client = createClient();
  for (const question of QUESTIONS) {
    const answer = await answerQuestion(client, question);
    const checks = checkQuotes(answer, RULEBOOK);
    const ok = checks.filter((c) => c.verbatim).length;
    console.log(`Q: ${question}\nA: ${answer}\n   quotes verbatim: ${ok}/${checks.length}\n`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
