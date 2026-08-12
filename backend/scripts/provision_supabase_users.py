"""Provision the demo users in Supabase Auth so browser Supabase login works.

Creates (idempotently) confirmed Supabase Auth users for the demo accounts with
their role in ``app_metadata.role``. The backend maps the Supabase UUID to a
MyCreditLens profile on first token (``_sync_supabase_user``). No password is
stored in MyCreditLens tables. Secret key is read from settings; never printed.

Run (from backend/):
    .venv\\Scripts\\python -m scripts.provision_supabase_users
"""

from __future__ import annotations

import httpx

from app.config import settings

DEMO_USERS = [
    ("admin@mycreditlens.com", "admin"),
    ("analyst@mycreditlens.com", "credit_analyst"),
    ("compliance@mycreditlens.com", "compliance_reviewer"),
    ("borrower@example.com", "borrower"),
]
PASSWORD = "DemoPass123!"


def main() -> None:
    if not (settings.supabase_url and settings.supabase_secret_key):
        print("Supabase not configured (SUPABASE_SECRET_KEY missing) — skipping provisioning.")
        return
    base = settings.supabase_url
    h = {
        "apikey": settings.supabase_secret_key,
        "Authorization": f"Bearer {settings.supabase_secret_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30, verify=settings.supabase_verify_ssl) as c:
        # Map existing users by email so we can update instead of duplicate.
        existing = {}
        page = 1
        while True:
            r = c.get(f"{base}/auth/v1/admin/users?page={page}&per_page=200", headers=h)
            users = r.json().get("users", []) if r.status_code == 200 else []
            for u in users:
                existing[u.get("email")] = u.get("id")
            if len(users) < 200:
                break
            page += 1
        for email, role in DEMO_USERS:
            if email in existing:
                uid = existing[email]
                c.put(
                    f"{base}/auth/v1/admin/users/{uid}",
                    headers=h,
                    json={"password": PASSWORD, "email_confirm": True, "app_metadata": {"role": role}},
                )
                print(f"  updated  {email} ({role})")
            else:
                r = c.post(
                    f"{base}/auth/v1/admin/users",
                    headers=h,
                    json={"email": email, "password": PASSWORD, "email_confirm": True, "app_metadata": {"role": role}},
                )
                print(f"  created  {email} ({role}): {r.status_code}")
    print("Supabase demo users provisioned.")


if __name__ == "__main__":
    main()
