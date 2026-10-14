// The four shop tools as VoltAgent tools; each delegates to the Shop class.
import { createTool } from "@voltagent/core";
import { z } from "zod";
import type { Shop } from "./shop/store.ts";

export function createShopTools(shop: Shop) {
  const checkServiceMenu = createTool({
    name: "check_service_menu",
    description: "List repair services with price and duration. Optional keyword filter, e.g. 'brake' or 'tyre'.",
    parameters: z.object({
      query: z.string().optional().describe("Keywords to filter the menu; omit for the full menu"),
    }),
    execute: async ({ query }) => shop.checkServiceMenu(query),
  });

  const findOpenSlot = createTool({
    name: "find_open_slot",
    description: "Find up to three open workshop slots for a service id (e.g. SVC-BRAKE), optionally on or after a date.",
    parameters: z.object({
      service_id: z.string().describe("Service id from check_service_menu, like SVC-TUNE"),
      on_or_after: z.string().optional().describe("ISO date YYYY-MM-DD; omit for the earliest"),
    }),
    execute: async ({ service_id, on_or_after }) => shop.findOpenSlot(service_id, on_or_after),
  });

  const bookRepair = createTool({
    name: "book_repair",
    description:
      "Book a repair into an open slot. Only call after the customer chose a slot and gave a name and a bike description.",
    parameters: z.object({
      slot_id: z.string().describe("Slot id from find_open_slot, like SLOT-3"),
      service_id: z.string().describe("Service id, like SVC-TUNE"),
      customer_name: z.string().describe("Customer's name"),
      bike: z.string().describe("Short bike description, e.g. 'green hybrid'"),
    }),
    execute: async (args) => shop.bookRepair(args),
  });

  const getBookingStatus = createTool({
    name: "get_booking_status",
    description: "Look up a booking by id (BK-xxxx): service, slot, and where the repair stands.",
    parameters: z.object({
      booking_id: z.string().describe("Booking id, like BK-2201"),
    }),
    execute: async ({ booking_id }) => shop.getBookingStatus(booking_id),
  });

  return { checkServiceMenu, findOpenSlot, bookRepair, getBookingStatus };
}
