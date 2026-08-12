"""Supabase JWKS token-verification tests.

Exercises `SupabaseTokenVerifier` against a LOCALLY generated ES256 (P-256)
keypair published as a mock JWKS — so signature / issuer / audience / expiry /
algorithm handling is validated without a live Supabase project.
"""

import base64
import time

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from jose import jwt

from app.config import settings
from app.services.supabase_auth_service import SupabaseTokenVerifier

pytestmark = pytest.mark.filterwarnings("ignore")

ISSUER = "https://dbkousrapsiplyezmcii.supabase.co/auth/v1"
AUDIENCE = "authenticated"
KID = "test-key-1"


def _b64u(n: int, length: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


@pytest.fixture()
def keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    nums = priv.public_key().public_numbers()
    jwk = {"kty": "EC", "crv": "P-256", "x": _b64u(nums.x, 32), "y": _b64u(nums.y, 32), "kid": KID, "alg": "ES256", "use": "sig"}
    return pem, jwk


@pytest.fixture()
def configure(monkeypatch, keypair):
    pem, jwk = keypair
    monkeypatch.setattr(settings, "supabase_jwks_url", ISSUER + "/.well-known/jwks.json")
    monkeypatch.setattr(settings, "supabase_jwt_issuer", ISSUER)
    monkeypatch.setattr(settings, "supabase_jwt_audience", AUDIENCE)

    async def fake_jwks():
        return {"keys": [jwk]}

    monkeypatch.setattr(SupabaseTokenVerifier, "_get_jwks", staticmethod(fake_jwks))
    return pem


def _token(pem, *, iss=ISSUER, aud=AUDIENCE, exp_delta=3600, sub="user-uuid-123", email="u@example.com"):
    now = int(time.time())
    claims = {"sub": sub, "email": email, "iss": iss, "aud": aud, "iat": now, "exp": now + exp_delta, "app_metadata": {"role": "borrower"}}
    return jwt.encode(claims, pem, algorithm="ES256", headers={"kid": KID})


async def _verify(token):
    return await SupabaseTokenVerifier.verify(token)


@pytest.mark.asyncio
async def test_valid_token_accepted(configure):
    claims = await _verify(_token(configure))
    assert claims["sub"] == "user-uuid-123"
    assert claims["email"] == "u@example.com"


@pytest.mark.asyncio
async def test_expired_token_rejected(configure):
    with pytest.raises(HTTPException) as exc:
        await _verify(_token(configure, exp_delta=-10))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_wrong_issuer_rejected(configure):
    with pytest.raises(HTTPException) as exc:
        await _verify(_token(configure, iss="https://evil.example/auth/v1"))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_wrong_audience_rejected(configure):
    with pytest.raises(HTTPException) as exc:
        await _verify(_token(configure, aud="anon"))
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_bad_signature_rejected(configure):
    # Sign with a different key than the one published in the JWKS.
    other = ec.generate_private_key(ec.SECP256R1())
    other_pem = other.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    forged = _token(other_pem)
    with pytest.raises(HTTPException) as exc:
        await _verify(forged)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_unconfigured_verifier_raises_503(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwks_url", None)
    with pytest.raises(HTTPException) as exc:
        await SupabaseTokenVerifier.verify("whatever")
    assert exc.value.status_code == 503
