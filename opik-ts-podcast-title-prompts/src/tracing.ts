import type OpenAI from "openai";
import { OpikSpanType, track } from "opik";
import type { Opik } from "opik";
import { MODEL, buildMessages, type ChatClient } from "./titles.js";

export const PROJECT_NAME = "opik-ts-podcast-title-prompts";

export function usageOf(completion: OpenAI.Chat.ChatCompletion): Record<string, number> {
  const usage = completion.usage;
  return {
    prompt_tokens: usage?.prompt_tokens ?? 0,
    completion_tokens: usage?.completion_tokens ?? 0,
    total_tokens: usage?.total_tokens ?? 0,
  };
}

// opik-openai logs completions as "general" spans, which Opik never prices. Logging the call
// ourselves as type "llm" with model, provider and usage is what fills in tokens and cost.
export function withOpikTracing(client: ChatClient): ChatClient {
  const tracedCreate = track(
    {
      name: "openai.chat.completions.create",
      type: OpikSpanType.Llm,
      projectName: PROJECT_NAME,
      enrichSpan: (completion: OpenAI.Chat.ChatCompletion) => ({
        model: completion.model,
        provider: "openai",
        usage: usageOf(completion),
      }),
    },
    (params: OpenAI.Chat.ChatCompletionCreateParamsNonStreaming) => client.chat.completions.create(params),
  );
  return { chat: { completions: { create: tracedCreate } } };
}

export type TitleGenerator = (summary: string) => Promise<string>;

// Fetches one prompt version from the library at call time and returns a title generator for it.
// getPrompt inside a track() context writes the prompt reference (name, version, commit) onto the
// trace, so each trace in Opik links back to the exact version that produced its title.
export function makeTitleGenerator(opik: Opik, client: ChatClient, version?: string): TitleGenerator {
  const traced = withOpikTracing(client);
  // A general span groups the call; the llm span nests under it, and inside a test-suite run
  // both nest under the suite's per-item trace.
  return track(
    { name: "generate_title", type: OpikSpanType.General, projectName: PROJECT_NAME },
    async (summary: string) => {
      const prompt = await opik.getPrompt({ name: "episode-title", version, projectName: PROJECT_NAME });
      if (!prompt) throw new Error("prompt episode-title not found; run registerPromptVersions first");
      const response = await traced.chat.completions.create({
        model: MODEL,
        messages: buildMessages(prompt.prompt, summary),
      });
      return response.choices[0]?.message.content?.trim() ?? "";
    },
  );
}
