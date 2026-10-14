// Wires BeeAI to Opik. Everything Opik-specific lives in this file.
//
// BeeAI's OpenInference instrumentation emits spans for each ReAct iteration, model call
// and tool call; a plain OTLP/HTTP exporter ships them to Opik's OpenTelemetry endpoint.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { BatchSpanProcessor, type ReadableSpan, type Span, type SpanProcessor } from "@opentelemetry/sdk-trace-base";
import { BeeAIInstrumentation } from "@arizeai/openinference-instrumentation-beeai";
import * as beeaiFramework from "beeai-framework";
import { MODEL } from "./config.ts";

export const OPIK_PROJECT = "beeai-home-energy-audit";

const otlpBase = (process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:5173/api/v1/private/otel").replace(/\/+$/, "");
const instrumentation = new BeeAIInstrumentation();

// Opik prices an llm span only when that one span carries a provider, a model and usage under
// keys its price table knows. BeeAI's instrumentation reports them under OpenInference keys
// (and the model not on every span), so token usage lands but total_estimated_cost stays null.
// This processor re-labels them on BeeAI's model-call spans: gen_ai.system, gen_ai.request.model
// and gen_ai.usage.* (renamed from llm.token_count.*), which Opik maps to provider, model, usage.
const USAGE_KEYS: Record<string, string> = {
  "llm.token_count.prompt": "gen_ai.usage.input_tokens",
  "llm.token_count.completion": "gen_ai.usage.output_tokens",
  "llm.token_count.total": "gen_ai.usage.total_tokens",
};
export const providerTagger: SpanProcessor = {
  onStart(span: Span) {
    if (/^backend\.openai\.chat\.(start|success)/.test(span.name)) {
      span.setAttribute("gen_ai.system", "openai");
      span.setAttribute("gen_ai.request.model", MODEL);
    }
  },
  onEnd(span: ReadableSpan) {
    const attrs = span.attributes as Record<string, unknown>;
    for (const [from, to] of Object.entries(USAGE_KEYS)) {
      if (attrs[from] !== undefined) {
        attrs[to] = attrs[from];
        delete attrs[from];
      }
    }
  },
  forceFlush: async () => {},
  shutdown: async () => {},
};

// The OTLP exporter sends spans to Opik; the headers pick the workspace and the project
// ("projectName") the traces land in. A local self-hosted Opik needs no Authorization header.
const exporter = new OTLPTraceExporter({
  url: `${otlpBase}/v1/traces`,
  headers: {
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
    projectName: OPIK_PROJECT,
  },
});

// NodeSDK + BeeAIInstrumentation turn each ReAct iteration, model call and tool call into spans.
const sdk = new NodeSDK({
  spanProcessors: [providerTagger, new BatchSpanProcessor(exporter)],
  instrumentations: [instrumentation],
});
sdk.start();

// tsx loads beeai-framework before the instrumentation's module hook can see it,
// so patch the already-imported module explicitly.
instrumentation.manuallyInstrument(beeaiFramework);

export async function flushTracing(): Promise<void> {
  await sdk.shutdown();
}
