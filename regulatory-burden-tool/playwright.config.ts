import { defineConfig, devices } from "@playwright/test";

// End-to-end tests run against the production build (so the Content-Security-Policy is active).
// Chromium is preinstalled at PLAYWRIGHT_BROWSERS_PATH; @playwright/test is pinned to match it.
export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:4173",
    trace: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run build && npx vite preview --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
