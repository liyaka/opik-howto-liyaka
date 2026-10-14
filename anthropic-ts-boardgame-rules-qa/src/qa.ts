import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";

export const MODEL = "claude-haiku-4-5-20251001";

export const RULEBOOK = readFileSync(
  fileURLToPath(new URL("../data/rulebook.md", import.meta.url)),
  "utf8",
);

export function buildSystemPrompt(rulebook: string): string {
  return `You are the rules referee for the board game Lanternfall. The complete \
rulebook is reproduced below.

Rules for your answers:
- Answer only from the rulebook. If it does not cover the question, say so plainly \
instead of guessing.
- Every ruling must be backed by a citation: an excerpt from the rulebook wrapped in \
<quote>...</quote> tags, copied character for character.
- Keep it short: the ruling first, then the supporting quote(s).

<rulebook>
${rulebook}
</rulebook>`;
}

export interface Answerer {
  messages: {
    create(params: Anthropic.MessageCreateParamsNonStreaming): Promise<Anthropic.Message>;
  };
}

export function createClient(): Anthropic {
  return new Anthropic();
}

export async function answerQuestion(
  client: Answerer,
  question: string,
  rulebook: string = RULEBOOK,
): Promise<string> {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: buildSystemPrompt(rulebook),
    messages: [{ role: "user", content: question }],
  });
  return response.content.flatMap((b) => (b.type === "text" ? [b.text] : [])).join("\n");
}
