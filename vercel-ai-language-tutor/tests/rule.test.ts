import { describe, expect, it } from "vitest";
import { ensureRule, ruleBody, RULE_NAME } from "../lib/rule";

function fakeOpik(existingRule: boolean) {
  const calls: { method: string; path: string }[] = [];
  const fetchImpl = (async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname.replace("/api", "");
    const method = init?.method ?? "GET";
    calls.push({ method, path });
    let body: unknown = {};
    if (path.endsWith("/projects")) body = { content: [{ id: "p1", name: "proj" }] };
    if (path.endsWith("/evaluators") && method === "GET") {
      body = { content: existingRule || calls.some((c) => c.method === "POST") ? [{ id: "r1", name: RULE_NAME }] : [] };
    }
    return new Response(JSON.stringify(body), { status: 200 });
  }) as unknown as typeof fetch;
  return { calls, fetchImpl };
}

describe("online-evaluation rule", () => {
  it("scores every trace and is enabled", () => {
    const body = ruleBody("p1");
    expect(body.sampling_rate).toBe(1);
    expect(body.enabled).toBe(true);
    expect(body.code.variables).toEqual({ input: "input", output: "output" });
  });

  it("creates the rule once when missing", async () => {
    const { calls, fetchImpl } = fakeOpik(false);
    expect((await ensureRule("proj", fetchImpl)).created).toBe(true);
    expect(calls.filter((c) => c.method === "POST" && c.path.endsWith("/evaluators"))).toHaveLength(1);
  });

  it("updates instead of duplicating when the rule exists", async () => {
    const { calls, fetchImpl } = fakeOpik(true);
    expect((await ensureRule("proj", fetchImpl)).created).toBe(false);
    expect(calls.some((c) => c.method === "POST" && c.path.endsWith("/evaluators"))).toBe(false);
    expect(calls.some((c) => c.method === "PATCH")).toBe(true);
  });
});
