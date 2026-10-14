import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";
import { buildSystemPrompt, type MuseumFacts } from "./museum.js";
import { opik } from "./tracing.js";

export const MODEL = "gpt-4o-mini";

// The only surface the bot needs from the OpenAI client, so tests can stub it.
export interface ChatClient {
  chat: {
    completions: {
      create(args: {
        model: string;
        messages: ChatCompletionMessageParam[];
      }): Promise<{
        choices: { message: { content: string | null } }[];
        usage?: { prompt_tokens: number; completion_tokens: number };
      }>;
    };
  };
}

export interface Turn {
  reply: string;
  traceId: string;
  promptTokens: number;
  completionTokens: number;
}

export class VisitorDesk {
  readonly messages: ChatCompletionMessageParam[];

  constructor(
    readonly conversationId: string,
    facts: MuseumFacts,
    private readonly client: ChatClient = new OpenAI() as unknown as ChatClient,
  ) {
    this.messages = [{ role: "system", content: buildSystemPrompt(facts) }];
  }

  async answer(question: string): Promise<Turn> {
    this.messages.push({ role: "user", content: question });

    // One trace per turn. Sharing threadId across a conversation's traces is what
    // makes the Threads tab show them as one chat transcript.
    const trace = opik.trace({
      name: "visitor-desk-turn",
      threadId: this.conversationId,
      input: { question },
    });

    // The llm span is logged by hand: opik-openai records the completion as a "general"
    // span, which Opik never prices. Type "llm" plus model, provider and usage is what
    // makes the backend fill in total_estimated_cost for this turn.
    const span = trace.span({
      name: "answer-visitor",
      type: "llm",
      model: MODEL,
      provider: "openai",
      input: { messages: [...this.messages] },
    });

    const response = await this.client.chat.completions.create({
      model: MODEL,
      messages: this.messages,
    });
    const reply = response.choices[0]?.message.content ?? "";
    this.messages.push({ role: "assistant", content: reply });

    const promptTokens = response.usage?.prompt_tokens ?? 0;
    const completionTokens = response.usage?.completion_tokens ?? 0;
    span.update({
      output: { reply },
      usage: {
        prompt_tokens: promptTokens,
        completion_tokens: completionTokens,
        total_tokens: promptTokens + completionTokens,
      },
    });
    span.end();

    // Output on the trace is what the thread view shows as the assistant message.
    trace.update({ output: { reply } });
    trace.end();
    return {
      reply,
      traceId: trace.data.id,
      promptTokens,
      completionTokens,
    };
  }
}
