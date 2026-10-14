import OpenAI from "openai";

export const MODEL = "gpt-4o-mini";

// The only surface the generator needs from the OpenAI client, so tests can stub it.
export interface ChatClient {
  chat: {
    completions: {
      create(params: OpenAI.Chat.ChatCompletionCreateParamsNonStreaming): Promise<OpenAI.Chat.ChatCompletion>;
    };
  };
}

export function createClient(): ChatClient {
  return new OpenAI();
}

export function buildMessages(systemPrompt: string, summary: string): OpenAI.Chat.ChatCompletionMessageParam[] {
  return [
    { role: "system", content: systemPrompt },
    { role: "user", content: `Episode summary:\n${summary}` },
  ];
}

export async function generateTitle(client: ChatClient, systemPrompt: string, summary: string): Promise<string> {
  const response = await client.chat.completions.create({
    model: MODEL,
    messages: buildMessages(systemPrompt, summary),
  });
  return response.choices[0]?.message.content?.trim() ?? "";
}
