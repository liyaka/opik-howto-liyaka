import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { getBalanceTool, listTransactionsTool, freezeCardTool } from "./tools.ts";

export const SYSTEM_PROMPT =
  "You are the virtual assistant for Larkspur Credit Union, a small fictional retail bank. " +
  "Ground every answer in tool results; never guess a balance, a transaction or a card id. " +
  "Customers give you their account id. Call get_balance first to see an account's cards, and " +
  "list_transactions to review activity. Only call freeze_card when the customer explicitly asks " +
  "to freeze or block a card or says it is lost or stolen, and use the card id from get_balance. " +
  "Be calm and concise: 2-4 sentences, no bullet lists.";

export const bankingAgent = new Agent({
  id: "banking-agent",
  name: "larkspur-banking-agent",
  instructions: SYSTEM_PROMPT,
  model: openai("gpt-4o-mini"),
  tools: { getBalanceTool, listTransactionsTool, freezeCardTool },
});
