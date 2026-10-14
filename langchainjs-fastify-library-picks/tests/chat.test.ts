import { afterEach, describe, expect, it } from "vitest";
import { FakeListChatModel } from "@langchain/core/utils/testing";
import type { BaseMessage } from "@langchain/core/messages";
import type { ChatResult } from "@langchain/core/outputs";
import type { CallbackManagerForLLMRun } from "@langchain/core/callbacks/manager";
import { buildApp } from "../src/server.js";

// Records the messages the chain sends to the model, then replies from a list.
class RecordingModel extends FakeListChatModel {
  seen: BaseMessage[][] = [];
  async _generate(
    messages: BaseMessage[],
    options?: this["ParsedCallOptions"],
    runManager?: CallbackManagerForLLMRun,
  ): Promise<ChatResult> {
    this.seen.push(messages);
    return super._generate(messages, options, runManager);
  }
}

// Real HTTP on an ephemeral port: Fastify's app.inject() pulls in an ESM-only
// dependency that Node 20.16 cannot require(), so the tests use fetch instead.
const apps: ReturnType<typeof buildApp>[] = [];
afterEach(async () => {
  await Promise.all(apps.splice(0).map((a) => a.close()));
});

async function post(app: ReturnType<typeof buildApp>, payload: unknown) {
  if (!apps.includes(app)) {
    await app.listen({ port: 0, host: "127.0.0.1" });
    apps.push(app);
  }
  const address = app.server.address() as { port: number };
  const res = await fetch(`http://127.0.0.1:${address.port}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return { statusCode: res.status, json: async () => res.json() };
}

describe("POST /chat", () => {
  it("rejects a body without sessionId", async () => {
    const app = buildApp(new RecordingModel({ responses: ["x"] }));
    const res = await post(app, { message: "hi" });
    expect(res.statusCode).toBe(400);
  });

  // OPIK_TRACK_DISABLE=true is set in vitest.config.ts, so the OpikCallbackHandler
  // attached to every turn is a no-op: this runs offline with no Opik server.
  it("answers with tracking disabled and returns a plain string reply", async () => {
    const app = buildApp(new RecordingModel({ responses: ["Try Salt Road Almanac."] }));
    const res = await post(app, { message: "cozy mystery by the sea", sessionId: "s1" });
    expect(res.statusCode).toBe(200);
    expect(await res.json()).toEqual({ reply: "Try Salt Road Almanac.", sessionId: "s1" });
  });

  it("carries earlier turns and catalog matches into the next prompt", async () => {
    const model = new RecordingModel({ responses: ["first", "second"] });
    const app = buildApp(model);
    await post(app, { message: "cozy mystery by the sea", sessionId: "s2" });
    await post(app, { message: "anything shorter?", sessionId: "s2" });

    const second = model.seen[1].map((m) => String(m.content)).join("\n");
    expect(second).toContain("cozy mystery by the sea");
    expect(second).toContain("first");
    // retrieval for the follow-up still sees the earlier request
    expect(second).toContain("Salt Road Almanac");
  });

  it("keeps sessions separate", async () => {
    const model = new RecordingModel({ responses: ["a", "b"] });
    const app = buildApp(model);
    await post(app, { message: "robots in space", sessionId: "one" });
    await post(app, { message: "hello", sessionId: "two" });
    expect(model.seen[1].map((m) => String(m.content)).join("\n")).not.toContain("robots in space");
  });
});
