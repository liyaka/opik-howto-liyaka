import { describe, expect, it } from "vitest";
import { Shop, loadShopData } from "../src/shop/store.ts";

const fresh = () => new Shop(loadShopData());

describe("shop logic", () => {
  it("filters the service menu by keyword", () => {
    const { services } = fresh().checkServiceMenu("brake") as { services: { id: string }[] };
    expect(services.map((s) => s.id)).toEqual(["SVC-TUNE", "SVC-BRAKE"]);
  });

  it("finds only open slots on or after a date", () => {
    const result = fresh().findOpenSlot("svc-tune", "2026-03-11") as { slots: { id: string }[] };
    expect(result.slots.map((s) => s.id)).toEqual(["SLOT-5", "SLOT-6"]);
  });

  it("books a slot once and refuses a double booking", () => {
    const shop = fresh();
    const args = { slot_id: "SLOT-3", service_id: "SVC-TUNE", customer_name: "Priya Nair", bike: "green hybrid" };
    const first = shop.bookRepair(args) as { booking_id: string; price_usd: number };
    expect(first).toMatchObject({ booking_id: "BK-2203", price_usd: 65 });
    expect(shop.bookRepair(args)).toHaveProperty("error");
    expect(shop.getBookingStatus("bk-2203")).toMatchObject({ status: "booked", date: "2026-03-10" });
  });

  it("reports unknown bookings as errors the model can recover from", () => {
    expect(fresh().getBookingStatus("BK-9999")).toHaveProperty("error");
  });
});
