import { defineConfig } from "vitest/config";
import { costingParameters } from "./costing-params-plugin";

export default defineConfig({
  plugins: [costingParameters()],
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
});
