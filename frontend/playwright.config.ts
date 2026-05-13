import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  use: {
    baseURL: "http://127.0.0.1:3210",
    trace: "on-first-retry",
  },
  webServer: {
    command:
      "cmd /c cd /d \"C:\\Users\\ahadb\\Documents\\New project 3\\frontend\" && npx next start --hostname 127.0.0.1 --port 3210",
    port: 3210,
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
