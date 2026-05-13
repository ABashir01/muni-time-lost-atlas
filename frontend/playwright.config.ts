import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  use: {
    baseURL: "http://127.0.0.1:3210",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command:
        "cmd /c \"\"C:\\Users\\ahadb\\Documents\\New project 3\\.venv\\Scripts\\python.exe\" -m uvicorn muni_lta_api.app:create_app --factory --host 127.0.0.1 --port 8000\"",
      cwd: "C:\\Users\\ahadb\\Documents\\New project 3",
      env: {
        PYTHONPATH: "C:\\Users\\ahadb\\Documents\\New project 3\\api\\src",
      },
      reuseExistingServer: true,
      timeout: 120_000,
      url: "http://127.0.0.1:8000/health",
    },
    {
      command: "npx.cmd next start --hostname 127.0.0.1 --port 3210",
      cwd: "C:\\Users\\ahadb\\Documents\\New project 3\\frontend",
      reuseExistingServer: true,
      timeout: 120_000,
      url: "http://127.0.0.1:3210",
    },
  ],
});
