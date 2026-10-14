// Next.js calls register() once at server start. The OTel setup needs Node APIs,
// so it is skipped in the Edge runtime.
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { registerTutorTelemetry } = await import("./lib/telemetry");
    registerTutorTelemetry();
  }
}
