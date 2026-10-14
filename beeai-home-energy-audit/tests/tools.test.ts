import { describe, expect, it } from "vitest";
import { buildPrompt } from "../src/agent.ts";
import { auditTools, estimateSavingsTool, getMeterReadings } from "../src/tools.ts";

describe("audit tools and prompt", () => {
  it("exposes the four tools by name", () => {
    expect(auditTools.map((t) => t.name)).toEqual([
      "get_meter_readings",
      "get_appliance_inventory",
      "lookup_tariff",
      "estimate_savings",
    ]);
  });

  it("runs a tool directly (no tracing configured, so nothing leaves the process)", async () => {
    const out = await getMeterReadings.run({ household_id: "HH-102", months: 3 });
    expect(JSON.parse(out.getTextContent()).readings).toHaveLength(3);
  });

  it("returns an error payload for an unknown household", async () => {
    const out = await estimateSavingsTool.run({ household_id: "HH-000", fix: "pool-pump-schedule" });
    expect(out.getTextContent()).toContain("Unknown household");
  });

  it("tells the agent which fixes do apply when it prices the wrong one", async () => {
    const out = await estimateSavingsTool.run({ household_id: "HH-101", fix: "pool-pump-schedule" });
    expect(out.getTextContent()).toContain("ev-offpeak-schedule");
  });

  it("puts the household and complaint in the prompt", () => {
    const prompt = buildPrompt("HH-103", "bill too high");
    expect(prompt).toContain("HH-103");
    expect(prompt).toContain("bill too high");
  });
});
