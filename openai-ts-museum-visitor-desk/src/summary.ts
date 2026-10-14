import type { Turn } from "./bot.js";

export interface ConversationSummary {
  turns: number;
  promptTokens: number;
  completionTokens: number;
  promptTokensPerTurn: number[];
}

// Every turn re-sends the whole history, so prompt tokens grow turn by turn.
export function summarize(turns: Turn[]): ConversationSummary {
  return {
    turns: turns.length,
    promptTokens: turns.reduce((n, t) => n + t.promptTokens, 0),
    completionTokens: turns.reduce((n, t) => n + t.completionTokens, 0),
    promptTokensPerTurn: turns.map((t) => t.promptTokens),
  };
}
