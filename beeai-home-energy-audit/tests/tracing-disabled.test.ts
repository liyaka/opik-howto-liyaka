import { describe, expect, it, vi } from "vitest";

// OTEL_SDK_DISABLED=true makes NodeSDK.start() a no-op, so no spans are exported to Opik.
// Set before the static imports below; loading beeai-framework happens at collection time,
// not inside a test, so a busy machine cannot trip the per-test timeout.
vi.hoisted(() => {
  process.env.OTEL_SDK_DISABLED = "true";
});
import { flushTracing, providerTagger } from "../src/tracing.ts";
import { lookupTariff } from "../src/tools.ts";

describe("tracing switched off", () => {
  it("still runs tools when the OTel SDK is disabled", async () => {
    const out = await lookupTariff.run({ household_id: "HH-101" });
    expect(JSON.parse(out.getTextContent()).peak_rate_per_kwh).toBe(0.46);
    await flushTracing();
  });
});

describe("Opik cost mapping", () => {
  it("relabels OpenInference token counts as gen_ai.usage keys", () => {
    const attrs: Record<string, unknown> = { "llm.token_count.prompt": 10, "llm.token_count.completion": 4 };
    providerTagger.onEnd({ attributes: attrs } as never);
    expect(attrs).toEqual({ "gen_ai.usage.input_tokens": 10, "gen_ai.usage.output_tokens": 4 });
  });

  it("tags model-call spans with provider and model", () => {
    const set: Record<string, unknown> = {};
    providerTagger.onStart({ name: "backend.openai.chat.success", setAttribute: (k: string, v: unknown) => (set[k] = v) } as never, {} as never);
    expect(set).toEqual({ "gen_ai.system": "openai", "gen_ai.request.model": "gpt-4o-mini" });
  });
});
