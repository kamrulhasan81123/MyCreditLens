from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings


class SupabaseTokenVerifier:
    """Verifies Supabase ECC access tokens against the project's JWKS."""

    _jwks: dict[str, Any] | None = None
    _jwks_expires_at: float = 0
    _cache_seconds = 3600

    @classmethod
    async def verify(cls, token: str) -> dict[str, Any]:
        if not settings.supabase_jwks_url or not settings.supabase_jwt_issuer:
            raise HTTPException(status_code=503, detail="Supabase JWT verification is not configured")
        try:
            header = jwt.get_unverified_header(token)
            key_id = header.get("kid")
            algorithm = header.get("alg")
            if not key_id or algorithm != "ES256":
                raise HTTPException(status_code=401, detail="Unsupported Supabase token")
            jwks = await cls._get_jwks()
            key = next((candidate for candidate in jwks.get("keys", []) if candidate.get("kid") == key_id), None)
            if not key:
                cls._jwks_expires_at = 0
                jwks = await cls._get_jwks()
                key = next((candidate for candidate in jwks.get("keys", []) if candidate.get("kid") == key_id), None)
            if not key:
                raise HTTPException(status_code=401, detail="Supabase signing key not found")
            options = {"verify_aud": bool(settings.supabase_jwt_audience)}
            return jwt.decode(
                token,
                key,
                algorithms=["ES256"],
                issuer=settings.supabase_jwt_issuer,
                audience=settings.supabase_jwt_audience,
                options=options,
            )
        except HTTPException:
            raise
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase token") from exc

    @classmethod
    async def _get_jwks(cls) -> dict[str, Any]:
        now = time.monotonic()
        if cls._jwks and now < cls._jwks_expires_at:
            return cls._jwks
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=settings.supabase_verify_ssl) as client:
                response = await client.get(settings.supabase_jwks_url)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="Supabase signing keys are unavailable") from exc
        if not isinstance(payload.get("keys"), list):
            raise HTTPException(status_code=503, detail="Supabase JWKS response is invalid")
        cls._jwks = payload
        cls._jwks_expires_at = now + cls._cache_seconds
        return payload
