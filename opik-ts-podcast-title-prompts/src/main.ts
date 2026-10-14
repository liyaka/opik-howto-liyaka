import { config } from "dotenv";

config({ path: new URL("../../.env", import.meta.url).pathname });
config({ path: new URL("../.env", import.meta.url).pathname });

import { Opik, flushAll, type TestSuiteResult } from "opik";
import { loadEpisodes } from "./episodes.js";
import { PROMPT_NAME, registerPromptVersions } from "./prompts.js";
import { buildSuite, runSuiteForVersion } from "./suite.js";
import { createClient } from "./titles.js";
import { PROJECT_NAME, makeTitleGenerator } from "./tracing.js";

function report(label: string, result: TestSuiteResult): void {
  console.log(
    `${label}: ${((result.passRate ?? 0) * 100).toFixed(0)}% pass rate (${result.itemsPassed}/${result.itemsTotal} items passed)`,
  );
  for (const item of result.itemResults.values()) {
    const first = item.testResults[0];
    const out = first?.testCase.taskOutput["output"];
    console.log(`  [${item.passed ? "PASS" : "FAIL"}] ${JSON.stringify(out)} (${item.runsPassed}/${item.runsTotal} runs)`);
  }
  // Per-assertion tally over every judged run, to see which rule each version breaks.
  const tally = new Map<string, { passed: number; total: number }>();
  for (const item of result.itemResults.values()) {
    for (const run of item.testResults) {
      for (const s of run.scoreResults) {
        const t = tally.get(s.name) ?? { passed: 0, total: 0 };
        t.total += 1;
        if (!s.scoringFailed && s.value === 1) t.passed += 1;
        tally.set(s.name, t);
      }
    }
  }
  for (const [name, t] of tally) console.log(`    ${t.passed}/${t.total} runs pass: ${name}`);
  if (result.experimentUrl) console.log(`  experiment: ${result.experimentUrl}`);
}

async function main(): Promise<void> {
  // The client sets the project for prompts, the suite and its experiments.
  const opik = new Opik({ projectName: PROJECT_NAME });
  const openai = createClient();

  // 1. Prompt library: two immutable versions of "episode-title".
  const { v1, v2 } = await registerPromptVersions(opik);
  console.log(`${PROMPT_NAME}: registered ${v1.version} and ${v2.version}`);

  // 2. One traced generation with the latest version, to see a single trace.
  const sample = loadEpisodes()[0]!;
  console.log(`Latest prompt on ${sample.slug}: ${await makeTitleGenerator(opik, openai)(sample.summary)}\n`);

  // 3. One suite, run once per prompt version. Each run is an experiment.
  const suite = await buildSuite(opik);
  const r1 = await runSuiteForVersion(suite, v1, makeTitleGenerator(opik, openai, "v1"));
  const r2 = await runSuiteForVersion(suite, v2, makeTitleGenerator(opik, openai, "v2"));
  report(`${PROMPT_NAME} v1`, r1);
  report(`${PROMPT_NAME} v2`, r2);

  // Traces and spans are batched in memory; flush before exit or the last ones never arrive
  // (flushAll covers both the suite client and the track() client).
  await flushAll();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
