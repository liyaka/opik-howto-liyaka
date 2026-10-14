import { describe, expect, it } from "vitest";
import type { Opik } from "opik";
import { loadEpisodes } from "../src/episodes.js";
import { PROMPT_V1, PROMPT_V2 } from "../src/prompts.js";
import { GLOBAL_ASSERTIONS } from "../src/suite.js";
import { MODEL, buildMessages, generateTitle, type ChatClient } from "../src/titles.js";
import { makeTitleGenerator, usageOf } from "../src/tracing.js";

function stubClient(text: string, calls: unknown[] = []): ChatClient {
  return {
    chat: {
      completions: {
        create: async (params) => {
          calls.push(params);
          return {
            id: "c1",
            object: "chat.completion",
            created: 0,
            model: MODEL,
            choices: [{ index: 0, finish_reason: "stop", logprobs: null, message: { role: "assistant", content: text, refusal: null } }],
            usage: { prompt_tokens: 10, completion_tokens: 4, total_tokens: 14 },
          };
        },
      },
    },
  };
}

describe("title generator", () => {
  it("sends the prompt as system message and the summary as user message", async () => {
    const calls: Array<{ messages: unknown }> = [];
    const title = await generateTitle(stubClient("  A Quiet Crossing \n", calls), PROMPT_V2, "Summary text");
    expect(title).toBe("A Quiet Crossing");
    expect(calls[0]?.messages).toEqual(buildMessages(PROMPT_V2, "Summary text"));
  });

  it("maps OpenAI token counts to Opik usage keys", () => {
    const usage = usageOf({ usage: { prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 } } as never);
    expect(usage).toEqual({ prompt_tokens: 7, completion_tokens: 3, total_tokens: 10 });
  });

  it("v2 adds rules that v1 lacks, and neither contains a template placeholder", () => {
    expect(PROMPT_V2).toContain("At most 7 words");
    expect(PROMPT_V1).not.toContain("At most 7 words");
    expect(PROMPT_V1 + PROMPT_V2).not.toContain("{{");
  });

  it("ships six episodes with unique slugs and uses no reserved id field", () => {
    const episodes = loadEpisodes();
    expect(episodes).toHaveLength(6);
    expect(new Set(episodes.map((e) => e.slug)).size).toBe(6);
    expect(episodes.every((e) => !("id" in e))).toBe(true);
    expect(GLOBAL_ASSERTIONS.length).toBeGreaterThan(0);
  });

  it("calls through a traced generator when tracking is disabled", async () => {
    const opik = { getPrompt: async () => ({ prompt: PROMPT_V2 }) } as unknown as Opik;
    const generate = makeTitleGenerator(opik, stubClient("Traced But Offline"), "v2");
    await expect(generate("Anything")).resolves.toBe("Traced But Offline");
  });
});
