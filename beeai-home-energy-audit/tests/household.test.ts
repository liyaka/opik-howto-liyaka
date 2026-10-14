import { describe, expect, it } from "vitest";
import { applianceReport, estimateSavings, findHousehold, findTariff, readingsFor } from "../src/household.ts";

describe("household data", () => {
  it("finds households case-insensitively and rejects unknown ids", () => {
    expect(findHousehold("hh-101")?.family).toBe("Okafor");
    expect(findHousehold("HH-999")).toBeUndefined();
  });

  it("reports the month-over-month jump behind the doubled bill", () => {
    const { readings, change_vs_previous_month_pct } = readingsFor(findHousehold("HH-101")!, 2);
    expect(readings).toHaveLength(2);
    expect(change_vs_previous_month_pct).toBe(86);
  });

  it("estimates monthly kWh per appliance", () => {
    const pump = applianceReport(findHousehold("HH-103")!).find((a) => a.name.startsWith("Pool pump"));
    expect(pump?.est_kwh_per_month).toBe(792);
  });

  it("prices a load-shift on the time-of-use tariff", () => {
    expect(findTariff("HH-101")?.id).toBe("TOU-EVENING");
    const est = estimateSavings("HH-101", "ev-offpeak-schedule");
    expect(est?.monthly_saving_usd).toBe(189);
    expect(est?.payback_months).toBe(0);
  });

  it("refuses a fix that does not apply to the household", () => {
    expect(estimateSavings("HH-101", "pool-pump-schedule")).toBeUndefined();
  });

  it("returns undefined for an unknown fix", () => {
    expect(estimateSavings("HH-101", "nope")).toBeUndefined();
  });
});
