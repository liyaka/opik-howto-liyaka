import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { PinoLogger } from "@mastra/loggers";
import { LibSQLStore } from "@mastra/libsql";
import { bankingAgent } from "./agent.ts";

export const PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";

// Tracing is off when OPIK_TRACK_DISABLE=true, so offline runs and tests never try to reach Opik.
export const tracingEnabled = () => process.env.OPIK_TRACK_DISABLE?.toLowerCase() !== "true";

export function buildObservability(): Observability | undefined {
  if (!tracingEnabled()) return undefined;

  // Opik Cloud by default; OPIK_URL_OVERRIDE points the same exporter at a self-hosted Opik.
  const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
  const headers: Record<string, string> = {
    // Comet-Workspace picks the workspace; projectName decides which Opik project receives the traces.
    "Comet-Workspace": process.env.OPIK_WORKSPACE_NAME ?? process.env.OPIK_WORKSPACE ?? "default",
    projectName: PROJECT_NAME,
  };
  // Opik Cloud needs the key; a local self-hosted Opik takes no Authorization header.
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

  return new Observability({
    configs: {
      default: {
        serviceName: PROJECT_NAME,
        exporters: [
          // OtelExporter ships Mastra's agent, LLM and tool spans to Opik's OTLP endpoint as an
          // invoke_agent > agent_step > chat / execute_tool tree.
          new OtelExporter({
            provider: {
              custom: {
                endpoint: `${opikBase}/v1/private/otel/v1/traces`,
                protocol: "http/json",
                headers,
              },
            },
          }),
        ],
      },
    },
  });
}

export const mastra = new Mastra({
  agents: { bankingAgent },
  storage: new LibSQLStore({ id: "memory-store", url: ":memory:" }),
  logger: new PinoLogger({ name: "Mastra", level: "warn" }),
  observability: buildObservability(),
});
