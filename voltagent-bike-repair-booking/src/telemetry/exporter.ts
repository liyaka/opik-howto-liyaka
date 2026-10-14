import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { mapVoltAgentAttributes, type Attributes, type MappingOptions } from "./mapping.ts";

// Wraps the real OTLP exporter and rewrites each span's attributes just before export,
// so VoltAgent's spans reach Opik with gen_ai.* usage, model and provider attached.
export class GenAIMappingExporter implements SpanExporter {
  constructor(
    private readonly inner: SpanExporter,
    private readonly options: MappingOptions,
  ) {}

  export(spans: ReadableSpan[], resultCallback: Parameters<SpanExporter["export"]>[1]): void {
    const mapped = spans.map((span) =>
      // Delegate to the original span and shadow only `attributes`, leaving the span untouched for other processors.
      Object.create(span, {
        attributes: { value: mapVoltAgentAttributes(span.attributes as Attributes, this.options) },
      }) as ReadableSpan,
    );
    this.inner.export(mapped, resultCallback);
  }

  shutdown(): Promise<void> {
    return this.inner.shutdown();
  }

  forceFlush(): Promise<void> {
    return this.inner.forceFlush?.() ?? Promise.resolve();
  }
}
