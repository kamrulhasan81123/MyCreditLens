from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RefreshTokenRequest, UserCreate, UserLogin, TokenResponse, UserOut, PasswordChange
from app.dependencies import get_current_user
from app.models.user import User
from app.services.auth_service import AuthService, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user (borrower or lender)."""
    service = AuthService(db)
    await service.register(user_data)
    return await service.login(UserLogin(email=user_data.email, password=user_data.password))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive JWT token."""
    service = AuthService(db)
    return await service.login(credentials)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a local JWT refresh token."""
    service = AuthService(db)
    return await service.refresh_access_token(data.refresh_token)


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    service = AuthService(db)
    await service.change_password(token, data)
    return {"message": "Password changed successfully"}
