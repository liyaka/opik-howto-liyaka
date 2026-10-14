import { beforeEach, describe, expect, it } from "vitest";
import { freezeCard, getBalance, listTransactions, resetBank } from "../src/bank.ts";

beforeEach(() => resetBank());

describe("bank logic", () => {
  it("returns the balance and cards, normalising the id", () => {
    const res: any = getBalance(" acc-3001 ");
    expect(res.balance).toBe(2481.37);
    expect(res.cards[0]).toMatchObject({ card_id: "CRD-7788", status: "active" });
  });

  it("reports unknown accounts instead of throwing", () => {
    expect(getBalance("ACC-0000")).toHaveProperty("error");
    expect(listTransactions("ACC-0000")).toHaveProperty("error");
  });

  it("lists transactions newest first and respects the limit", () => {
    const res: any = listTransactions("ACC-3001", 2);
    expect(res.count).toBe(2);
    expect(res.transactions.map((t: any) => t.txn_id)).toEqual(["T-9001", "T-9002"]);
  });

  it("freezes a card and is idempotent", () => {
    const first: any = freezeCard("CRD-9021", "stolen wallet");
    expect(first).toMatchObject({ status: "frozen", already_frozen: false });
    expect((freezeCard("CRD-9021", "again") as any).already_frozen).toBe(true);
    expect((getBalance("ACC-4410") as any).cards.find((c: any) => c.card_id === "CRD-9022").status).toBe("active");
  });
});
