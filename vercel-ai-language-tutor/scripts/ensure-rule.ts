import { loadEnv } from "./env";
loadEnv();
const { ensureRule, RULE_NAME } = await import("../lib/rule");
const { PROJECT_NAME } = await import("../lib/telemetry");

const { id, created } = await ensureRule(PROJECT_NAME);
console.log(`${created ? "Created" : "Updated"} online-evaluation rule ${RULE_NAME} (${id}) on ${PROJECT_NAME}`);
