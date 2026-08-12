"""Supabase Storage service (server-side, privileged).

Uses the Supabase **service-role** key for privileged storage administration
(bucket creation, upload, signed URLs, deletion). The service key is read from
settings (backend/.env) and is NEVER exposed to the browser or returned in any
response. Buckets are private; retrieval is via short-lived signed URLs.

If Supabase Storage is not configured (no service key), `is_configured()` is
False and callers fall back to the local storage path.
"""

from __future__ import annotations

import hashlib

import httpx
from fastapi import HTTPException, status

from app.config import settings

BUCKETS = ["financial-documents", "appeal-documents", "generated-reports", "consent-evidence"]

ALLOWED_MIME = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/octet-stream",
}

DEFAULT_SIGNED_URL_TTL = 3600


class SupabaseStorageService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.supabase_url and settings.supabase_secret_key)

    @staticmethod
    def _client() -> httpx.Client:
        if not SupabaseStorageService.is_configured():
            raise HTTPException(status_code=503, detail="Supabase Storage is not configured")
        headers = {
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
        }
        return httpx.Client(base_url=f"{settings.supabase_url}/storage/v1", headers=headers, timeout=30, verify=settings.supabase_verify_ssl)

    # ------------------------------------------------------------------
    @staticmethod
    def object_path(borrower_id: str, application_id: str, file_id: str, *, appeal_id: str | None = None) -> str:
        # {organisation_scope}/{application_id}/{file_id}; borrower_id stands in
        # for organisation scope (no organisation table in the current schema).
        if appeal_id:
            return f"{borrower_id}/{application_id}/appeals/{appeal_id}/{file_id}"
        return f"{borrower_id}/{application_id}/{file_id}"

    @staticmethod
    def validate_mime(content_type: str | None) -> str:
        ct = (content_type or "application/octet-stream").split(";")[0].strip().lower()
        if ct not in ALLOWED_MIME:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported file type: {ct}")
        return ct

    @classmethod
    def ensure_buckets(cls) -> list[str]:
        created = []
        with cls._client() as c:
            existing = {b["name"] for b in c.get("/bucket").json()}
            for b in BUCKETS:
                if b not in existing:
                    r = c.post("/bucket", json={"id": b, "name": b, "public": False})
                    if r.status_code in (200, 201):
                        created.append(b)
        return created

    @classmethod
    def upload(cls, bucket: str, object_path: str, content: bytes, content_type: str | None) -> dict:
        ct = cls.validate_mime(content_type)
        digest = hashlib.sha256(content).hexdigest()
        with cls._client() as c:
            r = c.post(
                f"/object/{bucket}/{object_path}",
                content=content,
                headers={"Content-Type": ct, "x-upsert": "true"},
            )
            if r.status_code not in (200, 201):
                raise HTTPException(status_code=502, detail=f"Storage upload failed ({r.status_code})")
        return {"bucket": bucket, "path": object_path, "sha256": digest, "size": len(content), "content_type": ct}

    @classmethod
    def signed_url(cls, bucket: str, object_path: str, expires_in: int = DEFAULT_SIGNED_URL_TTL) -> str:
        with cls._client() as c:
            r = c.post(f"/object/sign/{bucket}/{object_path}", json={"expiresIn": expires_in})
            if r.status_code != 200:
                raise HTTPException(status_code=404, detail="Object not found or cannot be signed")
            signed = r.json().get("signedURL") or r.json().get("signedUrl")
        # Storage returns a path relative to /storage/v1; make it absolute.
        return f"{settings.supabase_url}/storage/v1{signed}" if signed and signed.startswith("/") else str(signed)

    @classmethod
    def delete(cls, bucket: str, object_path: str) -> None:
        with cls._client() as c:
            r = c.request("DELETE", f"/object/{bucket}/{object_path}")
            if r.status_code not in (200, 204):
                raise HTTPException(status_code=502, detail="Storage delete failed")
