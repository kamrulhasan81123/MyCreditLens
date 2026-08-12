import { test, expect, request as pwRequest } from "@playwright/test"

/**
 * Full MyCreditLens workflow E2E (backend API). Isolated per run: registers a
 * unique borrower and its own application; staff logins use the demo seed.
 * Asserts on real backend values only — never fabricated data.
 */

const API = process.env.E2E_API_URL ?? "http://127.0.0.1:8000"
const PW = "DemoPass123!"

async function login(ctx: any, email: string, password = PW) {
  const r = await ctx.post(`${API}/api/v1/auth/login`, { data: { email, password } })
  expect(r.ok(), `login ${email}: ${r.status()}`).toBeTruthy()
  return (await r.json()).access_token as string
}
const auth = (t: string) => ({ Authorization: `Bearer ${t}` })

test("full borrower→analyst workflow over the API", async () => {
  const ctx = await pwRequest.newContext()
  const stamp = Date.now()
  const borrowerEmail = `e2e-${stamp}@example.com`

  // 1. Borrower authentication (register + implicit login token)
  const reg = await ctx.post(`${API}/api/v1/auth/register`, {
    data: { email: borrowerEmail, password: PW, full_name: "E2E Borrower", role: "borrower" },
  })
  expect(reg.status(), await reg.text()).toBe(201)
  const bTok = (await reg.json()).access_token as string

  // 2. Borrower profile (set fields required by the PD model)
  const upd = await ctx.put(`${API}/api/v1/borrowers/me`, {
    headers: auth(bTok),
    data: { date_of_birth: "1992-03-15", employment_type: "full_time", monthly_income_declared: 6500, employment_duration_years: 6, home_ownership: "OWN" },
  })
  expect(upd.ok(), await upd.text()).toBeTruthy()

  // 3. Create application → real id (not APP-2041)
  const ca = await ctx.post(`${API}/api/v1/applications/`, {
    headers: auth(bTok),
    data: { purpose: "Working capital", loan_intent: "PERSONAL", requested_amount: 9000, requested_term_months: 24 },
  })
  expect(ca.status(), await ca.text()).toBe(201)
  const appId = (await ca.json()).id as string
  expect(appId).not.toContain("APP-2041")

  // 4. Consent
  for (const c of ["bank_statement", "credit_scoring"]) {
    const r = await ctx.post(`${API}/api/v1/applications/${appId}/consents`, { headers: auth(bTok), data: { data_source_type: c } })
    expect(r.status(), await r.text()).toBe(201)
  }

  // 5-6. Financial-data upload + validation
  const csv = "date,description,amount\n2025-01-01,Salary,5000\n2025-02-01,Salary,5000\n2025-03-01,Salary,5000\n"
  const up = await ctx.post(`${API}/api/v1/applications/${appId}/data-sources?source_type=bank_statement`, {
    headers: auth(bTok),
    multipart: { file: { name: "stmt.csv", mimeType: "text/csv", buffer: Buffer.from(csv) } },
  })
  expect(up.ok(), await up.text()).toBeTruthy()
  expect((await up.json()).record_count).toBeGreaterThan(0)

  // 7. Submit
  const sub = await ctx.post(`${API}/api/v1/applications/${appId}/submit`, { headers: auth(bTok) })
  expect(sub.ok(), await sub.text()).toBeTruthy()

  // 8. Analyst authentication (demo seed)
  const aTok = await login(ctx, "analyst@mycreditlens.com")

  // 9. Analyst application view
  const view = await ctx.get(`${API}/api/v1/applications/${appId}`, { headers: auth(aTok) })
  expect(view.ok()).toBeTruthy()

  // 10. Real PD score
  const score = await ctx.post(`${API}/api/v1/applications/${appId}/score`, { headers: auth(aTok) })
  expect(score.status(), await score.text()).toBe(200)
  const sj = await score.json()
  expect(sj.model_version).toBe("2.0.0")
  expect(sj.probability_of_default).toBeGreaterThanOrEqual(0)
  expect(["low", "medium", "high"]).toContain(sj.risk_band)

  // 11. Real model metadata
  const meta = await ctx.get(`${API}/api/v1/models/metadata`, { headers: auth(aTok) })
  expect((await meta.json()).model_version).toBe("2.0.0")

  // 12. SHAP
  const expl = await ctx.get(`${API}/api/v1/applications/${appId}/explanations`, { headers: auth(aTok) })
  expect(expl.ok()).toBeTruthy()
  expect((await expl.json()).method).toBe("shap")

  // 13-14. Decision Room + data reliability (real or insufficient_data)
  const dr = await ctx.get(`${API}/api/v1/applications/${appId}/decision-room`, { headers: auth(aTok) })
  expect(dr.ok(), await dr.text()).toBeTruthy()
  const drj = await dr.json()
  expect(drj).toHaveProperty("data_reliability")
  expect(drj).toHaveProperty("cash_flow")
  expect(["available", "insufficient_data"]).toContain(drj.data_reliability.status)

  // 15. Stress test
  const stress = await ctx.post(`${API}/api/v1/applications/${appId}/stress-tests`, { headers: auth(aTok) })
  expect(stress.status()).toBe(200)

  // 16. Counterfactual
  const cf = await ctx.post(`${API}/api/v1/applications/${appId}/counterfactuals`, { headers: auth(aTok), data: { target_probability: 0.1, limit: 5 } })
  expect(cf.status()).toBe(200)

  // 17. Analyst decision
  const dec = await ctx.post(`${API}/api/v1/applications/${appId}/decisions`, { headers: auth(aTok), data: { decision: "rejected", reason: "E2E adverse decision for appeal path" } })
  expect(dec.status(), await dec.text()).toBe(201)

  // 18. Borrower explanation
  const bExpl = await ctx.get(`${API}/api/v1/applications/${appId}/explanations`, { headers: auth(bTok) })
  expect(bExpl.ok()).toBeTruthy()

  // 19. Borrower appeal
  const appeal = await ctx.post(`${API}/api/v1/applications/${appId}/appeals`, { headers: auth(bTok), data: { reason: "Requesting human review of the automated outcome." } })
  expect([200, 201]).toContain(appeal.status())

  // 20. Audit / timeline
  const timeline = drj.timeline as any[]
  expect(Array.isArray(timeline)).toBeTruthy()
  expect(timeline.length).toBeGreaterThan(0)

  await ctx.dispose()
})
