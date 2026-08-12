from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.config import settings
from app.models.borrower import Borrower, BorrowerType
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserLogin, PasswordChange
from app.services.supabase_auth_service import SupabaseTokenVerifier

def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate, *, allow_privileged: bool = False) -> User:
        existing = await self._get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        if user_data.role != UserRole.BORROWER.value and not allow_privileged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Privileged accounts must be created by an administrator",
            )
        user = User(
            email=user_data.email,
            hashed_password=_hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
        )
        self.db.add(user)
        await self.db.flush()
        if user.role == UserRole.BORROWER:
            self.db.add(Borrower(user_id=user.id, borrower_type=BorrowerType.INDIVIDUAL))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, credentials: UserLogin) -> dict:
        user = await self._get_user_by_email(credentials.email)
        if not user or not _verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        access_token = self._create_token(user, "access")
        refresh_token = self._create_token(user, "refresh")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": user,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = self._decode_token(refresh_token, expected_type="refresh")
        user = await self._get_user_by_id(payload["sub"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        access_token = self._create_token(user, "access")
        new_refresh_token = self._create_token(user, "refresh")
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": user,
        }

    async def get_current_user(self, token: str) -> User:
        if self._is_supabase_token(token):
            payload = await SupabaseTokenVerifier.verify(token)
            user = await self._sync_supabase_user(payload)
        else:
            payload = self._decode_token(token)
            user = await self._get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
        return user

    def _is_supabase_token(self, token: str) -> bool:
        if settings.auth_provider not in {"supabase", "hybrid"} or not settings.supabase_jwks_url:
            return False
        try:
            header = jwt.get_unverified_header(token)
            return header.get("alg") == "ES256" and bool(header.get("kid"))
        except JWTError:
            return False

    async def _sync_supabase_user(self, payload: dict) -> User:
        subject = payload.get("sub")
        email = payload.get("email")
        if not subject or not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase token is missing identity claims")
        user = await self._get_user_by_id(subject)
        if not user:
            user = await self._get_user_by_email(email)
        app_metadata = payload.get("app_metadata") or {}
        requested_role = app_metadata.get("role", UserRole.BORROWER.value)
        valid_roles = {role.value for role in UserRole}
        role = requested_role if requested_role in valid_roles else UserRole.BORROWER.value
        if user:
            user.email = email
            if role != UserRole.BORROWER.value:
                user.role = role
            await self.db.commit()
            await self.db.refresh(user)
            return user
        user_metadata = payload.get("user_metadata") or {}
        user = User(
            id=subject,
            email=email,
            hashed_password="supabase-managed",
            full_name=user_metadata.get("full_name") or email.split("@", 1)[0],
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        if role == UserRole.BORROWER.value:
            self.db.add(Borrower(user_id=user.id, borrower_type=BorrowerType.INDIVIDUAL))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, token: str, data: PasswordChange) -> None:
        user = await self.get_current_user(token)
        if not _verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        user.hashed_password = _hash_password(data.new_password)
        await self.db.commit()

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def _create_token(self, user: User, token_type: str) -> str:
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": getattr(user.role, "value", user.role),
            "type": token_type,
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def _decode_token(self, token: str, expected_type: str = "access") -> dict:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type", "access") != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            return payload
        except JWTError as exc:
            message = "Token has expired" if "expired" in str(exc).lower() else "Invalid token"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message,
            )
