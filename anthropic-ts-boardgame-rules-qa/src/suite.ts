import { Opik, runTests, type TestSuite, type TestSuiteResult } from "opik";
import { RULEBOOK } from "./qa.js";
import { QUESTIONS } from "./questions.js";
import { PROJECT_NAME } from "./tracing.js";

export const SUITE_NAME = "lanternfall-citation-checks";
export const JUDGE_MODEL = "claude-haiku-4-5";

// Plain-English assertions: an LLM judge grades each one per answer, no metric classes needed.
export const GLOBAL_ASSERTIONS = [
  "Every excerpt wrapped in <quote> tags in the response appears verbatim, character for character, in the provided rulebook context",
  "The quoted excerpts genuinely support the rulings given in the answer",
  "The response answers the question that was asked",
];

// Item-level assertions run on top of the global ones, for questions with one correct ruling.
export const ITEM_ASSERTIONS: Record<number, string[]> = {
  2: ["The response says Wick tokens cannot be traded; only cards can"],
  5: [
    "The response says the tied player with the most unspent Wick tokens wins",
    "The response says that if still tied, the players share the victory",
  ],
};

export async function buildSuite(client: Opik): Promise<TestSuite> {
  // A test suite is a dataset plus assertions; the judge settings and execution policy
  // live on the suite itself. runsPerItem 3 / passThreshold 2 absorbs judge flakiness.
  const suite = await client.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    globalAssertions: GLOBAL_ASSERTIONS,
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // Items carry the question and the rulebook, so the judge can check quotes against it.
  // insert() deduplicates identical items on re-runs.
  await suite.insert(
    QUESTIONS.map((question, i) => ({
      data: { question, context: RULEBOOK },
      assertions: ITEM_ASSERTIONS[i],
    })),
  );
  return suite;
}

export async function runSuite(
  suite: TestSuite,
  answer: (question: string) => Promise<string>,
): Promise<TestSuiteResult> {
  // runTests answers every item (3 runs each), has the judge grade each assertion, and
  // records an experiment of type test suite: one pass/fail per item, one trace per run.
  return runTests({
    testSuite: suite,
    task: async (item) => {
      const question = String(item["question"]);
      return { input: { question, context: item["context"] }, output: await answer(question) };
    },
    model: JUDGE_MODEL,
    taskThreads: 3,
  });
}
