// Builds the VoltAgent observability object that ships spans to Opik over OTLP.
import { VoltAgentObservability } from "@voltagent/core";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { GenAIMappingExporter } from "./exporter.ts";

export const DEFAULT_PROJECT = "voltagent-bike-repair-booking";

export function opikOtlpConfig(env: NodeJS.ProcessEnv = process.env) {
  const base = (env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
  const headers: Record<string, string> = {
    // Comet-Workspace picks the workspace, projectName picks the Opik project the traces land in.
    "Comet-Workspace": env.OPIK_WORKSPACE_NAME ?? env.OPIK_WORKSPACE ?? "default",
    projectName: env.OPIK_PROJECT_NAME ?? DEFAULT_PROJECT,
  };
  if (env.OPIK_API_KEY) headers.Authorization = env.OPIK_API_KEY;
  return { url: `${base}/v1/private/otel/v1/traces`, headers };
}

export function createObservability(env: NodeJS.ProcessEnv = process.env) {
  // OPIK_TRACK_DISABLE=true installs no span processor at all, so tests and offline runs send nothing to Opik.
  if (env.OPIK_TRACK_DISABLE === "true") {
    return new VoltAgentObservability({ serviceName: DEFAULT_PROJECT, spanProcessors: [] });
  }
  const exporter = new OTLPTraceExporter(opikOtlpConfig(env));
  // OTEL_GENAI_MAPPING=off sends VoltAgent's raw attributes, to see what Opik shows without the mapping.
  const mappingOn = env.OTEL_GENAI_MAPPING !== "off";
  return new VoltAgentObservability({
    serviceName: DEFAULT_PROJECT,
    // BatchSpanProcessor buffers spans and exports them in the background; observability.shutdown() must flush it.
    spanProcessors: [
      new BatchSpanProcessor(mappingOn ? new GenAIMappingExporter(exporter, { provider: "openai" }) : exporter),
    ],
  });
}
