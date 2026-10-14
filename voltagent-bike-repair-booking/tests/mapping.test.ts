import { describe, expect, it, vi } from "vitest";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { mapVoltAgentAttributes } from "../src/telemetry/mapping.ts";
import { GenAIMappingExporter } from "../src/telemetry/exporter.ts";
import { createObservability, opikOtlpConfig } from "../src/telemetry/setup.ts";
import { createShopTools } from "../src/tools.ts";
import { Shop, loadShopData } from "../src/shop/store.ts";

const options = { provider: "openai" };

const llmSpan = {
  "span.type": "llm",
  "llm.model": "gpt-4o-mini",
  "llm.messages": '[{"role":"user","content":"hi"}]',
  "llm.usage.prompt_tokens": 472,
  "llm.usage.completion_tokens": 76,
  "llm.usage.total_tokens": 548,
  "usage.prompt_context.total_tokens_estimated": 390,
  "entity.name": "agent",
};

describe("gen_ai.* attribute mapping", () => {
  it("maps llm usage, model and provider so Opik can price the span", () => {
    const out = mapVoltAgentAttributes(llmSpan, options);
    expect(out).toMatchObject({
      "gen_ai.request.model": "gpt-4o-mini",
      "gen_ai.provider.name": "openai",
      "gen_ai.usage.prompt_tokens": 472,
      "gen_ai.usage.completion_tokens": 76,
      "gen_ai.usage.total_tokens": 548,
    });
    expect(out).not.toHaveProperty("usage.prompt_context.total_tokens_estimated");
  });

  it("turns tool input and output into gen_ai.tool.call arguments and result", () => {
    const out = mapVoltAgentAttributes(
      { "span.type": "tool", "tool.name": "book_repair", input: '{"slot_id":"SLOT-3"}', output: '{"ok":true}', "tool.parameters": "{...}" },
      options,
    );
    expect(out["gen_ai.tool.call.arguments"]).toBe('{"slot_id":"SLOT-3"}');
    expect(out["gen_ai.tool.call.result"]).toBe('{"ok":true}');
    expect(out).not.toHaveProperty("tool.parameters");
    expect(out).not.toHaveProperty("input");
  });

  it("keeps only input and output on the agent root span", () => {
    const out = mapVoltAgentAttributes(
      { "entity.type": "agent", "entity.name": "agent", input: "q", output: "a", "agent.instructions": "long prompt" },
      options,
    );
    expect(out).toMatchObject({ input: "q", output: "a" });
    expect(out).not.toHaveProperty("agent.instructions");
  });

  it("exports mapped attributes without touching the original span", () => {
    const inner = { export: vi.fn(), shutdown: vi.fn(), forceFlush: vi.fn() } as unknown as SpanExporter;
    const span = { name: "llm:generateText", attributes: llmSpan, spanContext: () => ({ traceId: "t" }) } as unknown as ReadableSpan;
    new GenAIMappingExporter(inner, options).export([span], () => {});
    const sent = (inner.export as ReturnType<typeof vi.fn>).mock.calls[0]![0][0] as ReadableSpan;
    expect(sent.attributes["gen_ai.provider.name"]).toBe("openai");
    expect(sent.spanContext()).toEqual({ traceId: "t" });
    expect(span.attributes).toBe(llmSpan);
  });
});

describe("telemetry setup and tools with tracking disabled", () => {
  it("points the OTLP exporter at the project and workspace", () => {
    const cfg = opikOtlpConfig({ OPIK_URL_OVERRIDE: "http://localhost:5173/api/", OPIK_WORKSPACE: "default" });
    expect(cfg.url).toBe("http://localhost:5173/api/v1/private/otel/v1/traces");
    expect(cfg.headers).toEqual({ "Comet-Workspace": "default", projectName: "voltagent-bike-repair-booking" });
  });

  it("builds observability with OPIK_TRACK_DISABLE=true and still runs a tool", async () => {
    const observability = createObservability({ OPIK_TRACK_DISABLE: "true" });
    const { findOpenSlot } = createShopTools(new Shop(loadShopData()));
    const result = (await findOpenSlot.execute!({ service_id: "SVC-FLAT" }, undefined as never)) as { slots: unknown[] };
    expect(result.slots).toHaveLength(3);
    await observability.shutdown();
  });
});
