import { opikRequest, type Fetch } from "./opik-api";

export const RULE_NAME = "tutor_reply_quality";
export const SCORE_NAME = "tutor_reply_quality";

interface Project {
  id: string;
  name: string;
}

// The judge sees the whole trace input (system prompt + conversation) and the
// final reply, and returns one integer score that Opik stores as a feedback score.
export function ruleBody(projectId: string, model = "gpt-4o-mini") {
  return {
    type: "llm_as_judge",
    name: RULE_NAME,
    project_ids: [projectId],
    // sampling_rate 1 scores every trace; enabled must be true before traffic arrives.
    sampling_rate: 1,
    enabled: true,
    action: "evaluator",
    code: {
      model: { name: model, temperature: 0 },
      messages: [
        {
          role: "SYSTEM",
          content:
            "You grade a Spanish tutor's reply. Score 0-10. Give 9-10 when the reply does what the learner asked " +
            "(corrects a mistake with the fixed sentence, translates, or runs a quiz) and stays brief and on the lesson. " +
            "Deduct points for missing a mistake the learner made, wrong Spanish, or ignoring the request.",
        },
        {
          role: "USER",
          content: "Conversation sent to the tutor:\n{{input}}\n\nTutor reply:\n{{output}}",
        },
      ],
      variables: { input: "input", output: "output" },
      schema: [
        { name: SCORE_NAME, type: "INTEGER", description: "0-10 quality of the tutor's reply for what the learner asked." },
      ],
    },
  };
}

export async function ensureProject(name: string, fetchImpl: Fetch = fetch): Promise<Project> {
  const found = await opikRequest<{ content: Project[] }>(
    `/v1/private/projects?name=${encodeURIComponent(name)}&size=50`,
    {},
    fetchImpl,
  );
  const existing = found.content.find((p) => p.name === name);
  if (existing) return existing;
  await opikRequest("/v1/private/projects", { method: "POST", body: JSON.stringify({ name }) }, fetchImpl);
  const created = await opikRequest<{ content: Project[] }>(
    `/v1/private/projects?name=${encodeURIComponent(name)}&size=50`,
    {},
    fetchImpl,
  );
  const project = created.content.find((p) => p.name === name);
  if (!project) throw new Error(`Could not create Opik project ${name}`);
  return project;
}

// Find-or-create: re-running never duplicates the rule, and an existing rule is
// switched back on if someone disabled it. Returns the rule id.
export async function ensureRule(
  projectName: string,
  fetchImpl: Fetch = fetch,
): Promise<{ id: string; created: boolean }> {
  const project = await ensureProject(projectName, fetchImpl);
  const list = await opikRequest<{ content: { id: string; name: string; enabled?: boolean }[] }>(
    `/v1/private/automations/evaluators?project_id=${project.id}&name=${RULE_NAME}&size=50`,
    {},
    fetchImpl,
  );
  const existing = list.content.find((r) => r.name === RULE_NAME);
  if (existing) {
    await opikRequest(
      `/v1/private/automations/evaluators/${existing.id}`,
      { method: "PATCH", body: JSON.stringify(ruleBody(project.id)) },
      fetchImpl,
    );
    return { id: existing.id, created: false };
  }
  await opikRequest("/v1/private/automations/evaluators", { method: "POST", body: JSON.stringify(ruleBody(project.id)) }, fetchImpl);
  const again = await opikRequest<{ content: { id: string; name: string }[] }>(
    `/v1/private/automations/evaluators?project_id=${project.id}&name=${RULE_NAME}&size=50`,
    {},
    fetchImpl,
  );
  const rule = again.content.find((r) => r.name === RULE_NAME);
  if (!rule) throw new Error("Rule was created but not found afterwards");
  return { id: rule.id, created: true };
}
