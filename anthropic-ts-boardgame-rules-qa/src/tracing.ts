import type Anthropic from "@anthropic-ai/sdk";
import { OpikSpanType, track } from "opik";
import { answerQuestion, type Answerer } from "./qa.js";

export const PROJECT_NAME = "anthropic-ts-boardgame-rules-qa";

// There is no Opik integration package for the Anthropic TS SDK, so the call is traced by hand.
export function usageOf(message: Anthropic.Message): Record<string, number> {
  const { input_tokens, output_tokens } = message.usage;
  return {
    prompt_tokens: input_tokens,
    completion_tokens: output_tokens,
    total_tokens: input_tokens + output_tokens,
  };
}

export function withOpikTracing(client: Answerer): Answerer {
  // type "llm" + model + provider + usage is what lets Opik show tokens and estimate cost;
  // enrichSpan copies them off the response onto the span. Without it the span has no usage.
  const tracedCreate = track(
    {
      name: "anthropic.messages.create",
      type: OpikSpanType.Llm,
      projectName: PROJECT_NAME,
      enrichSpan: (message: Anthropic.Message) => ({
        model: message.model,
        provider: "anthropic",
        usage: usageOf(message),
      }),
    },
    (params: Anthropic.MessageCreateParamsNonStreaming) => client.messages.create(params),
  );
  return { messages: { create: tracedCreate } };
}

// A general span around the whole answer; the llm span above nests under it, and inside a
// test-suite run both nest under the suite's per-item trace.
export function makeTracedAnswerer(client: Answerer) {
  const traced = withOpikTracing(client);
  return track(
    { name: "answer_question", type: OpikSpanType.General, projectName: PROJECT_NAME },
    (question: string) => answerQuestion(traced, question),
  );
}
