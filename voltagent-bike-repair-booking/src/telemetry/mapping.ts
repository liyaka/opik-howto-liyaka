// Pure attribute translation from VoltAgent's span vocabulary to OpenTelemetry GenAI names.
// Opik's OTel ingestion only reads the gen_ai.* names for model, provider and token usage, so
// without this the usage and cost columns stay empty even though the spans arrive. It also
// copies any attribute it has no rule for into the span INPUT, so each span type is reduced
// to the attributes that should show up, with the useful leftovers moved to opik.metadata.*.
export type Attributes = Record<string, unknown>;

export type MappingOptions = {
  // Opik prices a span only when it knows the provider; VoltAgent's llm spans carry none.
  provider: string;
};

const pick = (source: Attributes, keys: string[]): Attributes =>
  Object.fromEntries(keys.filter((k) => source[k] !== undefined).map((k) => [k, source[k]]));

const defined = (attrs: Attributes): Attributes =>
  Object.fromEntries(Object.entries(attrs).filter(([, v]) => v !== undefined));

export function mapVoltAgentAttributes(source: Attributes, options: MappingOptions): Attributes {
  return defined(mapSpan(source, options));
}

function mapSpan(source: Attributes, { provider }: MappingOptions): Attributes {
  if (source["span.type"] === "llm") {
    const usage: Attributes = {};
    for (const key of ["prompt_tokens", "completion_tokens", "total_tokens"]) {
      if (source[`llm.usage.${key}`] !== undefined) usage[`gen_ai.usage.${key}`] = source[`llm.usage.${key}`];
    }
    return {
      "gen_ai.operation.name": "chat",
      "gen_ai.request.model": source["llm.model"],
      // provider.name is what makes Opik price the span: gen_ai.system carries the same value for older Opik versions.
      "gen_ai.provider.name": provider,
      "gen_ai.system": provider,
      ...usage,
      // VoltAgent keeps the request messages in llm.messages; gen_ai.prompt is what Opik shows as the span input.
      "gen_ai.prompt": source["llm.messages"],
      "opik.metadata.agent": source["entity.name"],
      "opik.metadata.finish_reason": source["llm.finish_reason"],
    };
  }

  if (source["span.type"] === "tool") {
    return {
      // gen_ai.tool.call.* makes Opik type the span as a tool and fill its input and output.
      "gen_ai.tool.name": source["tool.name"],
      "gen_ai.tool.call.arguments": source["input"] ?? "{}",
      "gen_ai.tool.call.result": source["output"],
      "opik.metadata.agent": source["entity.name"],
    };
  }

  if (source["entity.type"] === "agent" && source["input"] !== undefined) {
    // The agent run: plain input/output attributes become the trace input and output columns.
    return {
      ...pick(source, ["input", "output"]),
      "opik.metadata.agent": source["entity.name"],
      "opik.metadata.model": source["ai.model.name"],
    };
  }

  return source;
}
