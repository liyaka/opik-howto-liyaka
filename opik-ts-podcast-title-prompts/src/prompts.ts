import type { Opik, Prompt } from "opik";
import { PROJECT_NAME } from "./tracing.js";

export const PROMPT_NAME = "episode-title";

export const PROMPT_V1 = `You write episode titles for The Slow Lantern, a podcast of quiet stories about coastal towns and the people who keep them running.
Given an episode summary, write a catchy, attention-grabbing title that makes people want to press play.`;

export const PROMPT_V2 = `You write episode titles for The Slow Lantern, a podcast of quiet stories about coastal towns and the people who keep them running.
Given an episode summary, reply with the title and nothing else, following these rules exactly:
- At most 7 words.
- Plain text only: no colons, no quotation marks, no emoji, no hashtags.
- Name the concrete subject of the episode, using only details from the summary. Never use hype words such as secret, shocking, untold, incredible, or ultimate.`;

export const CHANGE_NOTES = {
  v1: "Initial version: catchy and attention-grabbing.",
  v2: "Add hard rules: 7 words max, plain text, concrete subject from the summary, no hype words.",
} as const;

// Registers each version once. The SDK creates a new version whenever the text differs from the
// latest one, so re-running the demo with v1 text after v2 exists would create a v3 copy of v1.
// Checking for the version number first keeps the library at exactly two versions.
export async function registerPromptVersions(client: Opik): Promise<{ v1: Prompt; v2: Prompt }> {
  const ensure = async (version: "v1" | "v2", text: string): Promise<Prompt> => {
    const existing = await client.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
    if (existing) return existing;
    // createPrompt writes an immutable version into the prompt library (Prompts page, with a diff view).
    return client.createPrompt({
      name: PROMPT_NAME,
      prompt: text,
      projectName: PROJECT_NAME,
      metadata: { change: CHANGE_NOTES[version] },
    });
  };
  const v1 = await ensure("v1", PROMPT_V1);
  const v2 = await ensure("v2", PROMPT_V2);
  return { v1, v2 };
}
