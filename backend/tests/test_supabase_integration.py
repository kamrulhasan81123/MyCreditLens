"""Live Supabase integration tests (network-dependent).

Skipped by default so the normal offline unit suite stays fast/hermetic. Run
explicitly with the env flag:

    RUN_SUPABASE_IT=1 .venv\\Scripts\\python -m pytest tests/test_supabase_integration.py -q

Requires backend/.env to have SUPABASE_URL, SUPABASE_SECRET_KEY,
SUPABASE_PUBLISHABLE_KEY (and JWKS/issuer/audience). No secret values are printed.
"""

import os
import time

import httpx
import pytest

from app.config import settings
from app.services.storage_service import SupabaseStorageService
from app.services.supabase_auth_service import SupabaseTokenVerifier

pytestmark = pytest.mark.filterwarnings("ignore")

RUN = os.environ.get("RUN_SUPABASE_IT") == "1"
requires_live = pytest.mark.skipif(
    not (RUN and SupabaseStorageService.is_configured()),
    reason="Set RUN_SUPABASE_IT=1 with Supabase creds to run live integration tests",
)


@requires_live
def test_storage_upload_signed_url_and_delete():
    SupabaseStorageService.ensure_buckets()
    path = SupabaseStorageService.object_path("it-borrower", "it-app", f"it_{int(time.time())}.csv")
    content = b"date,description,amount\n2025-01-01,Salary,5000\n"
    meta = SupabaseStorageService.upload("financial-documents", path, content, "text/csv")
    assert meta["size"] == len(content) and len(meta["sha256"]) == 64
    url = SupabaseStorageService.signed_url("financial-documents", path, 120)
    assert url.startswith(settings.supabase_url)
    with httpx.Client(verify=settings.supabase_verify_ssl, timeout=20) as c:
        r = c.get(url)
        assert r.status_code == 200
        assert r.content.strip() == content.strip()
    SupabaseStorageService.delete("financial-documents", path)


@requires_live
def test_storage_rejects_unsupported_mime():
    with pytest.raises(Exception):
        SupabaseStorageService.validate_mime("application/x-msdownload")


@requires_live
@pytest.mark.asyncio
async def test_supabase_auth_jwks_roundtrip():
    email = f"it-auth-{int(time.time())}@example.com"
    pw = "DemoPass123!x"
    base = settings.supabase_url
    admin_h = {"apikey": settings.supabase_secret_key, "Authorization": f"Bearer {settings.supabase_secret_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(verify=settings.supabase_verify_ssl, timeout=25) as c:
        cr = await c.post(f"{base}/auth/v1/admin/users", headers=admin_h, json={"email": email, "password": pw, "email_confirm": True, "app_metadata": {"role": "borrower"}})
        assert cr.status_code == 200, cr.text
        uid = cr.json()["id"]
        try:
            lr = await c.post(f"{base}/auth/v1/token?grant_type=password", headers={"apikey": settings.supabase_publishable_key, "Content-Type": "application/json"}, json={"email": email, "password": pw})
            assert lr.status_code == 200, lr.text
            token = lr.json()["access_token"]
            claims = await SupabaseTokenVerifier.verify(token)
            assert claims["sub"] == uid
            assert claims["iss"] == settings.supabase_jwt_issuer
            assert claims["aud"] == settings.supabase_jwt_audience
        finally:
            await c.delete(f"{base}/auth/v1/admin/users/{uid}", headers=admin_h)
