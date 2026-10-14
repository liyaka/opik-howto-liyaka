// The assistant's three tools: thin Mastra wrappers around src/bank.ts.
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { getBalance, listTransactions, freezeCard } from "./bank.ts";

export const getBalanceTool = createTool({
  id: "get_balance",
  description:
    "Get the current balance of a bank account by id (e.g. ACC-3001). Also lists the debit and " +
    "credit cards attached to the account with their ids and status.",
  inputSchema: z.object({
    account_id: z.string().describe("The account id, like ACC-3001"),
  }),
  execute: async ({ account_id }) => getBalance(account_id),
});

export const listTransactionsTool = createTool({
  id: "list_transactions",
  description: "List the most recent transactions on an account, newest first. Negative amounts are debits.",
  inputSchema: z.object({
    account_id: z.string().describe("The account id, like ACC-3001"),
    limit: z.number().int().min(1).max(10).optional().describe("How many transactions to return (default 5)"),
  }),
  execute: async ({ account_id, limit }) => listTransactions(account_id, limit),
});

export const freezeCardTool = createTool({
  id: "freeze_card",
  description:
    "Immediately freeze a card so it cannot be used for new purchases. Only call this when the " +
    "customer clearly asks to freeze or block a card, or reports it lost or stolen.",
  inputSchema: z.object({
    card_id: z.string().describe("The card id, like CRD-7788"),
    reason: z.string().describe("Why the customer wants the card frozen"),
  }),
  execute: async ({ card_id, reason }) => freezeCard(card_id, reason),
});
