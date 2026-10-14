import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { registerOTel } from "@vercel/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";

export const PROJECT_NAME = process.env.OPIK_PROJECT_NAME ?? "vercel-ai-language-tutor";

// Maps the runtimeContext the route passes in to span attributes Opik reads.
// threadId is what groups one learner session's turns into a single Opik thread.
export function enrichTutorSpan(ctx: { runtimeContext?: Record<string, unknown> }) {
  const attributes: Record<string, string> = {};
  const runtime = ctx.runtimeContext;
  if (runtime?.threadId != null) {
    attributes["ai.telemetry.metadata.threadId"] = String(runtime.threadId);
  }
  if (runtime?.traceName != null) {
    attributes["ai.telemetry.metadata.traceName"] = String(runtime.traceName);
  }
  if (runtime?.lessonId != null) {
    attributes["ai.telemetry.metadata.lessonId"] = String(runtime.lessonId);
  }
  return attributes;
}

export function registerTutorTelemetry() {
  // OpikExporter is the OTel trace exporter: it turns the AI SDK spans into Opik
  // traces and llm spans in PROJECT_NAME. Without it nothing leaves the process.
  registerOTel({
    serviceName: PROJECT_NAME,
    traceExporter: new OpikExporter({
      client: new Opik({ projectName: PROJECT_NAME }),
      tags: ["nextjs", "language-tutor"],
    }),
  });

  // AI SDK v7 emits no OTel spans until a telemetry integration is registered;
  // without this call the project stays empty even though the exporter is set up.
  registerTelemetry(new OpenTelemetry({ usage: true, enrichSpan: enrichTutorSpan }));
}

// OpikExporter.getSettings turns telemetry on for one call and names the trace;
// includeRuntimeContext forwards threadId/lessonId/traceName so enrichTutorSpan can see them.
export function tutorTelemetry(name = "tutor-turn") {
  return {
    ...OpikExporter.getSettings({ name }),
    includeRuntimeContext: { threadId: true, lessonId: true, traceName: true },
  };
}
