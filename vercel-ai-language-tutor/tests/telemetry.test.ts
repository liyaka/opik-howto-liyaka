import { describe, expect, it } from "vitest";
import { enrichTutorSpan, tutorTelemetry } from "../lib/telemetry";

describe("telemetry settings", () => {
  // OPIK_TRACK_DISABLE=true is set by the test script: building the traced call
  // settings must still work, so unit tests never need an Opik server.
  it("builds Opik telemetry settings with tracking disabled", () => {
    const settings = tutorTelemetry("tutor-turn");
    expect(settings.isEnabled).toBe(true);
    expect(settings.includeRuntimeContext).toEqual({ threadId: true, lessonId: true, traceName: true });
  });

  it("maps runtimeContext to span attributes", () => {
    expect(enrichTutorSpan({ runtimeContext: { threadId: "abc", lessonId: "cafe-ordering" } })).toEqual({
      "ai.telemetry.metadata.threadId": "abc",
      "ai.telemetry.metadata.lessonId": "cafe-ordering",
    });
    expect(enrichTutorSpan({})).toEqual({});
  });
});
