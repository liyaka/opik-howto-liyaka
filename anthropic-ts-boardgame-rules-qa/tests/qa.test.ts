import { describe, expect, it } from "vitest";
import type { Answerer } from "../src/qa.js";
import { MODEL, RULEBOOK, answerQuestion, buildSystemPrompt } from "../src/qa.js";
import { QUESTIONS } from "../src/questions.js";
import { ITEM_ASSERTIONS } from "../src/suite.js";
import { makeTracedAnswerer, usageOf } from "../src/tracing.js";

function stubClient(text: string, calls: unknown[] = []): Answerer {
  return {
    messages: {
      create: async (params) => {
        calls.push(params);
        return {
          id: "msg_1",
          type: "message",
          role: "assistant",
          model: MODEL,
          content: [{ type: "text", text, citations: null }],
          stop_reason: "end_turn",
          stop_sequence: null,
          usage: { input_tokens: 10, output_tokens: 5 },
        } as never;
      },
    },
  };
}

describe("qa", () => {
  it("puts the whole rulebook and the quoting rule into the system prompt", () => {
    const prompt = buildSystemPrompt(RULEBOOK);
    expect(prompt).toContain("<rulebook>");
    expect(prompt).toContain("Lanternfall");
    expect(prompt).toContain("<quote>...</quote>");
  });

  it("sends the question as the user message and returns the text", async () => {
    const calls: Array<{ messages: unknown }> = [];
    const answer = await answerQuestion(stubClient("hello", calls), "Who goes first?");
    expect(answer).toBe("hello");
    expect(calls[0]?.messages).toEqual([{ role: "user", content: "Who goes first?" }]);
  });

  it("maps Anthropic token counts to Opik usage keys", () => {
    const usage = usageOf({ usage: { input_tokens: 7, output_tokens: 3 } } as never);
    expect(usage).toEqual({ prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 });
  });

  it("calls through a traced answerer when tracking is disabled", async () => {
    const answer = makeTracedAnswerer(stubClient("traced but offline"));
    await expect(answer("Anything?")).resolves.toBe("traced but offline");
  });

  it("only attaches item assertions to questions that exist", () => {
    for (const index of Object.keys(ITEM_ASSERTIONS)) {
      expect(QUESTIONS[Number(index)]).toBeDefined();
    }
  });
});
