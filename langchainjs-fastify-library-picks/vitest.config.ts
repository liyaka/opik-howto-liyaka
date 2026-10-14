import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    // Documented Opik switch: with it set, the callback handler records nothing
    // and never contacts a server, so unit tests need no Opik and no keys.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
