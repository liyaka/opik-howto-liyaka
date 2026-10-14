import { describe, expect, it } from "vitest";
import { VisitorDesk, MODEL, type ChatClient } from "../src/bot.js";
import { buildFeedbackScores, toThumbs } from "../src/feedback.js";
import { buildSystemPrompt, loadFacts } from "../src/museum.js";
import { summarize } from "../src/summary.js";

function stubClient(replies: string[]): { client: ChatClient; calls: number[] } {
  const calls: number[] = [];
  let i = 0;
  const client: ChatClient = {
    chat: {
      completions: {
        async create({ model, messages }) {
          expect(model).toBe(MODEL);
          calls.push(messages.length);
          return {
            choices: [{ message: { content: replies[i++] ?? "" } }],
            usage: { prompt_tokens: 100 * messages.length, completion_tokens: 10 },
          };
        },
      },
    },
  };
  return { client, calls };
}

describe("museum facts", () => {
  it("puts every section into the system prompt", () => {
    const facts = loadFacts();
    const prompt = buildSystemPrompt(facts);
    expect(prompt).toContain(facts.name);
    expect(prompt).toContain("Thursday late opening");
    expect(prompt).toContain("Quiet hour");
    expect(prompt).toContain(facts.escalation);
  });
});

describe("VisitorDesk", () => {
  it("keeps history across turns and works with Opik tracking disabled", async () => {
    const { client, calls } = stubClient(["Open until 21:00.", "It is free."]);
    const desk = new VisitorDesk("t-1", loadFacts(), client);

    const first = await desk.answer("When do you close on Thursday?");
    const second = await desk.answer("And for under 12s?");

    expect(first.reply).toBe("Open until 21:00.");
    expect(second.reply).toBe("It is free.");
    // system + user, then system + user + assistant + user
    expect(calls).toEqual([2, 4]);
    expect(desk.messages.map((m) => m.role)).toEqual([
      "system", "user", "assistant", "user", "assistant",
    ]);
    expect(second.promptTokens).toBeGreaterThan(first.promptTokens);
  });
});

describe("summary and feedback", () => {
  it("sums tokens and keeps the per-turn growth", () => {
    const s = summarize([
      { reply: "a", traceId: "1", promptTokens: 400, completionTokens: 30 },
      { reply: "b", traceId: "2", promptTokens: 480, completionTokens: 50 },
    ]);
    expect(s).toEqual({
      turns: 2,
      promptTokens: 880,
      completionTokens: 80,
      promptTokensPerTurn: [400, 480],
    });
  });

  it("builds feedback score payloads", () => {
    expect(toThumbs(true)).toBe(1);
    expect(toThumbs(false)).toBe(0);
    expect(buildFeedbackScores([{ traceId: "abc", value: 1, reason: "nice" }])).toEqual([
      { id: "abc", name: "visitor-satisfaction", value: 1, reason: "nice" },
    ]);
  });
});
