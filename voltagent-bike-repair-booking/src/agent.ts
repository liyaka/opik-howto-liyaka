// The agent definition: model, instructions and tools. Nothing here knows about tracing.
import { Agent } from "@voltagent/core";
import { Shop, loadShopData } from "./shop/store.ts";
import { createShopTools } from "./tools.ts";

export const MODEL = "gpt-4o-mini";

export function createBookingAgent(shop = new Shop(loadShopData())) {
  return new Agent({
    name: "spokewise-booking-assistant",
    // VoltAgent's model router resolves this id to the AI SDK OpenAI provider (reads OPENAI_API_KEY).
    model: `openai/${MODEL}`,
    instructions:
      "You are the booking assistant for Spokewise Cycle Works, a neighbourhood bike repair shop. " +
      "Use the tools for every fact about services, prices, slots and bookings; never guess. " +
      "Offer slots from find_open_slot and only call book_repair once the customer picked one and " +
      "gave their name and a bike description. Repeat the booking id, date, time and price after booking. " +
      "Reply in 2-4 friendly sentences.",
    tools: createShopTools(shop),
  });
}
