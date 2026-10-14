import { Opik, runTests, type Prompt, type TestSuite, type TestSuiteResult } from "opik";
import { loadEpisodes } from "./episodes.js";
import { PROMPT_NAME } from "./prompts.js";
import { MODEL } from "./titles.js";
import { PROJECT_NAME, type TitleGenerator } from "./tracing.js";

export const SUITE_NAME = "episode-title-checks";
export const JUDGE_MODEL = "gpt-4o-mini";

// Plain-English assertions: an LLM judge grades each one for every title.
export const GLOBAL_ASSERTIONS = [
  "The title is 7 words or fewer",
  "The title is plain text: it contains no colon, no quotation marks, no emoji and no hashtag",
  "The title does not use hype words such as secret, shocking, untold, incredible, unveiling or ultimate",
  "The title is about the subject described in the episode summary",
];

export async function buildSuite(client: Opik): Promise<TestSuite> {
  // A test suite is a dataset plus assertions. runsPerItem 3 / passThreshold 2 absorbs judge
  // flakiness: an item passes when at least two of three judged runs pass.
  const suite = await client.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    globalAssertions: GLOBAL_ASSERTIONS,
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // insert() deduplicates identical items, so re-running the demo does not grow the dataset.
  await suite.insert(loadEpisodes().map((e) => ({ data: { slug: e.slug, summary: e.summary } })));
  return suite;
}

// Runs the same suite against one prompt version. Each call becomes one experiment, linked to the
// prompt version through `prompts`, so the Prompts page and the experiment point at each other.
export async function runSuiteForVersion(
  suite: TestSuite,
  prompt: Prompt,
  generate: TitleGenerator,
): Promise<TestSuiteResult> {
  return runTests({
    testSuite: suite,
    task: async (item) => {
      const summary = String(item["summary"]);
      return { input: { summary }, output: await generate(summary) };
    },
    experimentName: `${PROMPT_NAME}-v${prompt.version?.replace(/^v/, "") ?? "?"}`,
    experimentConfig: { prompt_version: prompt.version, prompt_commit: prompt.commit, model: MODEL },
    prompts: [prompt],
    model: JUDGE_MODEL,
    taskThreads: 3,
  });
}
