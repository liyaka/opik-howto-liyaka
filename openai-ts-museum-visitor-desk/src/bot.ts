import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";
import { buildSystemPrompt, type MuseumFacts } from "./museum.js";

export const MODEL = "gpt-4o-mini";

// The only surface the bot needs from the OpenAI client, so tests can stub it.
export interface ChatClient {
  chat: {
    completions: {
      create(args: {
        model: string;
        messages: ChatCompletionMessageParam[];
      }): Promise<{ choices: { message: { content: string | null } }[] }>;
    };
  };
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

  async answer(question: string): Promise<string> {
    this.messages.push({ role: "user", content: question });
    const response = await this.client.chat.completions.create({
      model: MODEL,
      messages: this.messages,
    });
    const reply = response.choices[0]?.message.content ?? "";
    this.messages.push({ role: "assistant", content: reply });
    return reply;
  }
}
