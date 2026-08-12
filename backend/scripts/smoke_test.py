"""Live API smoke test for the scoring vertical slice (§21).

Drives a running MyCreditLens server over HTTP and proves the whole workflow:
health -> auth -> self-serve borrower/application/consent/submit -> score (200)
-> persisted prediction -> explanation -> stress test -> counterfactual ->
decision -> audit log, plus a negative object-level authz check.

Usage (start the server first, then run):
    .venv\\Scripts\\python -m uvicorn app.main:app --port 8000
    .venv\\Scripts\\python scripts/smoke_test.py            # defaults to :8000
    .venv\\Scripts\\python scripts/smoke_test.py http://127.0.0.1:8100

Requires the demo users from `app.scripts.seed_demo` (admin/analyst logins).
"""

import sys
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def login(c, email, pw="DemoPass123!"):
    r = c.post(f"{BASE}/api/v1/auth/login", json={"email": email, "password": pw})
    r.raise_for_status()
    return r.json()["access_token"]


def h(t):
    return {"Authorization": f"Bearer {t}"}


def main():
    c = httpx.Client(timeout=30)
    out = []

    hm = c.get(f"{BASE}/health/model").json()
    out.append(("health/model", hm["status"], hm["model"]["model_version"]))
    assert hm["status"] == "ready", hm

    analyst = login(c, "analyst@mycreditlens.com")
    admin = login(c, "admin@mycreditlens.com")

    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    reg = c.post(
        f"{BASE}/api/v1/auth/register",
        json={"email": email, "password": "DemoPass123!", "full_name": "Smoke Borrower", "role": "borrower"},
    )
    reg.raise_for_status()
    borrower = reg.json()["access_token"]
    c.put(
        f"{BASE}/api/v1/borrowers/me",
        headers=h(borrower),
        json={
            "date_of_birth": "1992-03-15",
            "employment_type": "full_time",
            "monthly_income_declared": 6500,
            "employment_duration_years": 6,
            "home_ownership": "OWN",
        },
    ).raise_for_status()
    ca = c.post(
        f"{BASE}/api/v1/applications/",
        headers=h(borrower),
        json={"purpose": "Working capital", "loan_intent": "PERSONAL", "requested_amount": 9000, "requested_term_months": 24},
    )
    ca.raise_for_status()
    app_id = ca.json()["id"]
    for cst in ("bank_statement", "credit_scoring"):
        c.post(f"{BASE}/api/v1/applications/{app_id}/consents", headers=h(borrower), json={"data_source_type": cst}).raise_for_status()
    c.post(f"{BASE}/api/v1/applications/{app_id}/submit", headers=h(borrower)).raise_for_status()
    out.append(("self-serve application", email, app_id))

    score = c.post(f"{BASE}/api/v1/applications/{app_id}/score", headers=h(analyst))
    sj = score.json()
    out.append(("score status", score.status_code, f"PD={sj['probability_of_default']:.4f} band={sj['risk_band']}"))
    out.append(("score model_version", sj["model_version"], sj["model_name"]))
    out.append(("score fields", f"calib={sj['calibrated_probability']:.4f}", f"schema={sj['feature_schema_version']} ood={sj['is_ood']} unc={sj['uncertainty']:.3f}"))
    assert score.status_code == 200 and sj["model_version"] == "2.0.0"

    pred = c.get(f"{BASE}/api/v1/applications/{app_id}/predictions", headers=h(analyst)).json()
    out.append(("prediction persisted", pred["id"], pred["model_version"]))

    expl = c.get(f"{BASE}/api/v1/applications/{app_id}/explanations", headers=h(analyst))
    out.append(("explanation", expl.status_code, expl.json()["method"]))
    assert expl.status_code == 200

    stress = c.post(f"{BASE}/api/v1/applications/{app_id}/stress-tests", headers=h(analyst))
    out.append(("stress-test", stress.status_code, f"worst={stress.json()['worst_case_probability']:.4f}"))
    assert stress.status_code == 200

    cf = c.post(f"{BASE}/api/v1/applications/{app_id}/counterfactuals", headers=h(analyst), json={"target_probability": 0.1, "limit": 5})
    out.append(("counterfactual", cf.status_code, f"{len(cf.json()['scenarios'])} scenarios"))
    assert cf.status_code == 200

    dec = c.post(f"{BASE}/api/v1/applications/{app_id}/decisions", headers=h(analyst), json={"decision": "approved", "reason": "Smoke test approval"})
    out.append(("decision", dec.status_code, dec.json().get("decision")))
    assert dec.status_code == 201

    audit = c.get(f"{BASE}/api/v1/audit-logs", headers=h(admin))
    out.append(("audit-logs", audit.status_code, f"{len(audit.json())} entries"))
    assert audit.status_code == 200

    intruder = c.post(f"{BASE}/api/v1/auth/register", json={"email": f"intruder-{uuid.uuid4().hex[:6]}@example.com", "password": "DemoPass123!", "full_name": "Intruder X", "role": "borrower"})
    itok = intruder.json()["access_token"]
    ds = c.get(f"{BASE}/api/v1/applications/{app_id}/data-sources", headers=h(itok))
    out.append(("intruder data-sources (expect 404)", ds.status_code, ""))
    assert ds.status_code == 404

    print("\n=== SMOKE TEST RESULTS ===")
    for row in out:
        print(f"  {row[0]:38s} | {row[1]} | {row[2]}")
    print("\nALL SMOKE CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("SMOKE FAILED:", repr(e))
        sys.exit(1)
