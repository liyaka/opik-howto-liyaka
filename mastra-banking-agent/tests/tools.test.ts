import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { resetBank } from "../src/bank.ts";
import { freezeCardTool, getBalanceTool } from "../src/tools.ts";
import { buildObservability, tracingEnabled } from "../src/mastra.ts";

const ctx = {} as never;

beforeEach(() => {
  process.env.OPIK_TRACK_DISABLE = "true";
  resetBank();
});
afterEach(() => {
  delete process.env.OPIK_TRACK_DISABLE;
});

describe("tools and tracing switch", () => {
  it("runs a tool directly with tracking disabled", async () => {
    // Outside a Mastra run no span is opened, so the tool behaves like a plain function.
    const res: any = await getBalanceTool.execute!({ account_id: "ACC-4410" }, ctx);
    expect(res.balance).toBe(312.9);
    const frozen: any = await freezeCardTool.execute!({ card_id: "CRD-9021", reason: "lost" }, ctx);
    expect(frozen.status).toBe("frozen");
  });

  it("builds no Opik exporter when OPIK_TRACK_DISABLE=true", () => {
    expect(tracingEnabled()).toBe(false);
    expect(buildObservability()).toBeUndefined();
  });

  it("builds the exporter when tracking is on", () => {
    delete process.env.OPIK_TRACK_DISABLE;
    expect(tracingEnabled()).toBe(true);
    expect(buildObservability()).toBeDefined();
  });
});
