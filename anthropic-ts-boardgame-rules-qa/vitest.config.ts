import { defineConfig } from "vitest/config";

export default defineConfig({
  // Tracking off for the unit tests: @track-wrapped functions then just call through, no network.
  test: { env: { OPIK_TRACK_DISABLE: "true" } },
});
