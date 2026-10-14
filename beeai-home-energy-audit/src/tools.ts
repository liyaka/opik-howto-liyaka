// The four tools the audit agent can call. Each is a BeeAI DynamicTool, so when the
// OpenInference instrumentation is active every call becomes a `tool` span in Opik
// whose input is the arguments and whose output is the JSON returned here.
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import {
  applicableFixes,
  applianceReport,
  estimateSavings,
  findHousehold,
  findTariff,
  readingsFor,
} from "./household.ts";

const householdId = z.string().describe('Household id, e.g. "HH-101".');
const unknownHousehold = (id: string) =>
  new JSONToolOutput({ error: `Unknown household "${id}". Known ids: HH-101, HH-102, HH-103.` });

export const getMeterReadings = new DynamicTool({
  name: "get_meter_readings",
  description:
    "Monthly electricity usage in kWh for a household, newest last, with the change versus the previous month.",
  inputSchema: z.object({
    household_id: householdId,
    months: z.number().int().min(1).max(6).default(6).describe("How many recent months to return."),
  }),
  async handler({ household_id, months }) {
    const household = findHousehold(household_id);
    return household ? new JSONToolOutput(readingsFor(household, months)) : unknownHousehold(household_id);
  },
});

export const getApplianceInventory = new DynamicTool({
  name: "get_appliance_inventory",
  description:
    "List the major electrical appliances in a household with wattage, daily run hours, estimated monthly kWh and maintenance notes, plus the ids of the candidate fixes you can price.",
  inputSchema: z.object({ household_id: householdId }),
  async handler({ household_id }) {
    const household = findHousehold(household_id);
    return household
      ? new JSONToolOutput({
          appliances: applianceReport(household),
          candidate_fixes: applicableFixes(household.id),
        })
      : unknownHousehold(household_id);
  },
});

export const lookupTariff = new DynamicTool({
  name: "lookup_tariff",
  description:
    "The electricity tariff a household is on: peak and off-peak price per kWh, the peak window and the fixed monthly fee.",
  inputSchema: z.object({ household_id: householdId }),
  async handler({ household_id }) {
    const tariff = findTariff(household_id);
    return tariff ? new JSONToolOutput(tariff) : unknownHousehold(household_id);
  },
});

export const estimateSavingsTool = new DynamicTool({
  name: "estimate_savings",
  description:
    "Estimate the monthly dollar saving, upfront cost and payback period of one candidate fix for a household. " +
    "Use a fix id from the candidate_fixes list returned by get_appliance_inventory.",
  inputSchema: z.object({
    household_id: householdId,
    fix: z.string().describe("A fix id from candidate_fixes."),
  }),
  async handler({ household_id, fix }) {
    const estimate = estimateSavings(household_id, fix);
    if (estimate) return new JSONToolOutput(estimate);
    if (!findHousehold(household_id)) return unknownHousehold(household_id);
    return new JSONToolOutput({
      error: `Fix "${fix}" does not apply to ${household_id}. Applicable fixes: ${applicableFixes(household_id).join(", ")}.`,
    });
  },
});

export const auditTools = [getMeterReadings, getApplianceInventory, lookupTariff, estimateSavingsTool];
