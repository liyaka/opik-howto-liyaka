// Household data layer: loads the fictional fixtures and answers the questions
// the tools ask. Pure functions, no Opik, no BeeAI, so they are unit-testable offline.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface MeterReading {
  month: string;
  kwh: number;
}
export interface Appliance {
  name: string;
  watts: number;
  hours_per_day: number;
  notes: string;
}
export interface Household {
  id: string;
  family: string;
  home: string;
  tariff_id: string;
  meter_readings_kwh: MeterReading[];
  appliances: Appliance[];
}
export interface Tariff {
  id: string;
  name: string;
  peak_rate_per_kwh: number;
  offpeak_rate_per_kwh: number;
  peak_window: string;
  fixed_monthly_fee: number;
}
export interface Fix {
  id: string;
  label: string;
  kwh_saved_per_month: number;
  shift_peak_kwh_to_offpeak_per_month: number;
  upfront_cost: number;
  applies_to: string[];
}
interface Dataset {
  households: Household[];
  tariffs: Tariff[];
  fixes: Fix[];
}

const DATA_PATH = fileURLToPath(new URL("../data/households.json", import.meta.url));
const dataset: Dataset = JSON.parse(readFileSync(DATA_PATH, "utf8"));

export function findHousehold(id: string): Household | undefined {
  return dataset.households.find((h) => h.id.toLowerCase() === id.trim().toLowerCase());
}

export function readingsFor(
  household: Household,
  months: number,
): { readings: MeterReading[]; change_vs_previous_month_pct: number | null } {
  const readings = household.meter_readings_kwh.slice(-Math.max(1, months));
  const last = readings[readings.length - 1];
  const prev = readings[readings.length - 2];
  const change = prev && last ? Math.round(((last.kwh - prev.kwh) / prev.kwh) * 100) : null;
  return { readings, change_vs_previous_month_pct: change };
}

export function applianceReport(household: Household) {
  return household.appliances.map((a) => ({
    ...a,
    est_kwh_per_month: Math.round((a.watts * a.hours_per_day * 30) / 1000),
  }));
}

export function findTariff(householdId: string): Tariff | undefined {
  const household = findHousehold(householdId);
  return household && dataset.tariffs.find((t) => t.id === household.tariff_id);
}

export function applicableFixes(householdId: string): string[] {
  const id = householdId.trim().toUpperCase();
  return dataset.fixes.filter((f) => f.applies_to.includes(id)).map((f) => f.id);
}

export interface SavingsEstimate {
  fix: string;
  label: string;
  monthly_saving_usd: number;
  upfront_cost_usd: number;
  payback_months: number | null;
}

// Savings = kWh avoided at the peak rate, plus peak kWh moved to the off-peak rate.
export function estimateSavings(householdId: string, fixId: string): SavingsEstimate | undefined {
  const tariff = findTariff(householdId);
  const fix = dataset.fixes.find((f) => f.id === fixId);
  if (!tariff || !fix || !applicableFixes(householdId).includes(fix.id)) return undefined;
  const saving =
    fix.kwh_saved_per_month * tariff.peak_rate_per_kwh +
    fix.shift_peak_kwh_to_offpeak_per_month *
      (tariff.peak_rate_per_kwh - tariff.offpeak_rate_per_kwh);
  const monthly = Math.round(saving * 100) / 100;
  return {
    fix: fix.id,
    label: fix.label,
    monthly_saving_usd: monthly,
    upfront_cost_usd: fix.upfront_cost,
    payback_months: monthly > 0 ? Math.round((fix.upfront_cost / monthly) * 10) / 10 : null,
  };
}
