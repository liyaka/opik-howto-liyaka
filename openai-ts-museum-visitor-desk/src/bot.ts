import OpenAI from "openai";
import { trackOpenAI } from "opik-openai";
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

    // trackOpenAI with a parent trace: the completion becomes an llm span under this
    // trace, carrying model, token usage and (backend-computed) cost.
    const client = trackOpenAI(this.client, {
      client: opik,
      parent: trace,
      generationName: "answer-visitor",
    }) as ChatClient;

    const response = await client.chat.completions.create({
      model: MODEL,
      messages: this.messages,
    });
    const reply = response.choices[0]?.message.content ?? "";
    this.messages.push({ role: "assistant", content: reply });

    // Output on the trace is what the thread view shows as the assistant message.
    trace.update({ output: { reply } });
    trace.end();
    return {
      reply,
      traceId: trace.data.id,
      promptTokens: response.usage?.prompt_tokens ?? 0,
      completionTokens: response.usage?.completion_tokens ?? 0,
    };
  }
}
