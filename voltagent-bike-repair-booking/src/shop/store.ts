// Pure shop logic over the fictional JSON data: no framework, no telemetry.
// The tools in ../tools.ts are thin wrappers around these functions.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export type Service = {
  id: string;
  name: string;
  description: string;
  price_usd: number;
  duration_hours: number;
};
export type Slot = { id: string; date: string; time: string; mechanic: string; open: boolean };
export type Booking = {
  id: string;
  customer: string;
  bike: string;
  service_id: string;
  slot_id: string;
  status: "booked" | "in_progress" | "ready_for_pickup";
  note: string;
};
export type ShopData = { shop: string; services: Service[]; slots: Slot[]; bookings: Booking[] };

export function loadShopData(path = fileURLToPath(new URL("../../data/shop.json", import.meta.url))): ShopData {
  return JSON.parse(readFileSync(path, "utf8")) as ShopData;
}

export class Shop {
  private nextBooking: number;

  constructor(private readonly data: ShopData) {
    // Work on a copy so booking in one run never edits the loaded data.
    this.data = structuredClone(data);
    this.nextBooking = 2203;
  }

  checkServiceMenu(query?: string) {
    const terms = (query ?? "").toLowerCase().split(/\s+/).filter(Boolean);
    const services = this.data.services.filter((s) => {
      if (terms.length === 0) return true;
      const haystack = `${s.name} ${s.description}`.toLowerCase();
      return terms.some((t) => haystack.includes(t));
    });
    if (services.length === 0) return { services: [], note: `No service matches "${query}". Ask for the full menu.` };
    return { services };
  }

  findOpenSlot(serviceId: string, onOrAfter?: string) {
    const service = this.data.services.find((s) => s.id === serviceId.toUpperCase().trim());
    if (!service) return { error: `Unknown service ${serviceId}. Use check_service_menu to find the id.` };
    const slots = this.data.slots
      .filter((s) => s.open && (!onOrAfter || s.date >= onOrAfter))
      .slice(0, 3);
    if (slots.length === 0) return { service: service.name, slots: [], note: "No open slots on or after that date." };
    return { service: service.name, duration_hours: service.duration_hours, slots };
  }

  bookRepair(args: { slot_id: string; service_id: string; customer_name: string; bike: string }) {
    const service = this.data.services.find((s) => s.id === args.service_id.toUpperCase().trim());
    if (!service) return { error: `Unknown service ${args.service_id}.` };
    const slot = this.data.slots.find((s) => s.id === args.slot_id.toUpperCase().trim());
    if (!slot) return { error: `Unknown slot ${args.slot_id}.` };
    if (!slot.open) return { error: `Slot ${slot.id} is already taken. Use find_open_slot for another one.` };
    slot.open = false;
    const booking: Booking = {
      id: `BK-${this.nextBooking++}`,
      customer: args.customer_name,
      bike: args.bike,
      service_id: service.id,
      slot_id: slot.id,
      status: "booked",
      note: "Drop the bike off ten minutes before your slot.",
    };
    this.data.bookings.push(booking);
    return {
      booking_id: booking.id,
      service: service.name,
      price_usd: service.price_usd,
      date: slot.date,
      time: slot.time,
      mechanic: slot.mechanic,
    };
  }

  getBookingStatus(bookingId: string) {
    const booking = this.data.bookings.find((b) => b.id === bookingId.toUpperCase().trim());
    if (!booking) return { error: `No booking ${bookingId}. Booking ids look like BK-2201.` };
    const service = this.data.services.find((s) => s.id === booking.service_id);
    const slot = this.data.slots.find((s) => s.id === booking.slot_id);
    return {
      booking_id: booking.id,
      customer: booking.customer,
      bike: booking.bike,
      service: service?.name,
      date: slot?.date,
      time: slot?.time,
      status: booking.status,
      note: booking.note,
    };
  }
}
