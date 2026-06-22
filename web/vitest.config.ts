import { defineConfig } from "vitest/config";

// Minimal config: node environment is sufficient — egograph.ts is pure and
// client-safe (no DOM, no node:fs). Tests live alongside lib code as *.test.ts.
export default defineConfig({
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts"],
  },
});
