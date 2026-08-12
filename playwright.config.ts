import { defineConfig } from "@playwright/test"

const API = process.env.E2E_API_URL ?? "http://127.0.0.1:8000"

/**
 * E2E config. The primary spec drives the full MyCreditLens workflow through the
 * backend API (Playwright `request` fixture — reliable, no brittle UI selectors,
 * no browser download required). A backend webServer is started automatically
 * (reused if already running). It uses whatever backend/.env points at
 * (Supabase Postgres locally); staff logins rely on the demo seed.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: API },
  webServer: {
    command:
      process.platform === "win32"
        ? ".venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
        : ".venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
    cwd: "backend",
    url: `${API}/health`,
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
