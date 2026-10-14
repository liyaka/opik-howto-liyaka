import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // OPIK_TRACK_DISABLE turns the Opik SDK into a no-op so tests never need a server.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
