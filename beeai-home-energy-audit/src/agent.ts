// The audit agent: a BeeAI ReAct agent on gpt-4o-mini. A fresh agent (and fresh
// memory) per complaint keeps every complaint an independent trace in Opik.
import { ReActAgent } from "beeai-framework/agents/react/agent";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { MODEL } from "./config.ts";
import { auditTools } from "./tools.ts";

export function buildPrompt(householdId: string, complaint: string): string {
  return `You are a home-energy auditor triaging a customer complaint.

Household: ${householdId}
Complaint: "${complaint}"

Reason step by step: every step starts with a "Thought:" line, then you call one tool or give the final answer.
Work from evidence, not guesses. Pull the meter readings, the appliance inventory and the tariff
before you diagnose, and price each candidate fix that fits the evidence with estimate_savings (never price fixes the evidence does not point to).

Finish with a prioritized fix list, best payback first, formatted exactly like this:
Diagnosis: <one sentence>
1. <fix> - saves $<per month>/month, costs $<upfront>, payback <months> months
2. ...
(at most 3 fixes)`;
}

// agent.run() is one trace root in Opik (beeai-framework-main); each ReAct turn shows up as an
// iteration-N span holding that turn's model call and tool call.
export async function auditHousehold(householdId: string, complaint: string): Promise<string> {
  const agent = new ReActAgent({
    llm: new OpenAIChatModel(MODEL),
    tools: auditTools,
    memory: new UnconstrainedMemory(),
  });
  const response = await agent.run(
    { prompt: buildPrompt(householdId, complaint) },
    { execution: { maxRetriesPerStep: 3, totalMaxRetries: 10, maxIterations: 10 } },
  );
  return response.result.text;
}
