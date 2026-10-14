import { config } from "dotenv";

config({ path: new URL("../../.env", import.meta.url).pathname });
config({ path: new URL("../.env", import.meta.url).pathname });

import { Opik, flushAll } from "opik";
import { createClient } from "./qa.js";
import { buildSuite, runSuite } from "./suite.js";
import { PROJECT_NAME, makeTracedAnswerer } from "./tracing.js";

async function main(): Promise<void> {
  const opik = new Opik({ projectName: PROJECT_NAME });
  const answer = makeTracedAnswerer(createClient());
  const suite = await buildSuite(opik);
  const result = await runSuite(suite, answer);

  console.log(
    `Pass rate: ${((result.passRate ?? 0) * 100).toFixed(0)}% (${result.itemsPassed}/${result.itemsTotal} items passed)`,
  );
  for (const item of result.itemResults.values()) {
    const first = item.testResults[0];
    const question = (first?.testCase.taskOutput["input"] as { question: string }).question;
    console.log(`  [${item.passed ? "PASS" : "FAIL"}] ${question} (${item.runsPassed}/${item.runsTotal} runs)`);
    if (!item.passed) {
      const seen = new Set<string>();
      for (const run of item.testResults) {
        for (const s of run.scoreResults) {
          if ((s.scoringFailed || s.value !== 1) && !seen.has(s.name)) {
            seen.add(s.name);
            console.log(`         failed: ${s.name} - ${s.reason}`);
          }
        }
      }
    }
  }
  if (result.experimentUrl) console.log(`View the run: ${result.experimentUrl}`);

  // Traces and spans are batched in memory; flush before exit or the last ones never arrive (flushAll covers the suite client and the track() client).
  await flushAll();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
