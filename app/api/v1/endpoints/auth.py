import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, decode_token, get_current_user, get_required_user, hash_password, verify_password
from app.db.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import TokenResponse, UserLoginRequest, UserProfileResponse, UserRegisterRequest, UserUpdateRequest

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    if body.username:
        ex = await db.execute(select(User).where(User.username == body.username))
        if ex.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")
    if body.email:
        ex = await db.execute(select(User).where(User.email == body.email))
        if ex.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
    username=body.username,
    email=body.email,
    hashed_password=hash_password(body.password) if body.password else None,
    display_name=body.display_name,
    language=body.language,
    is_anonymous=body.is_anonymous,
    role=UserRole(body.role) if body.role else UserRole.CIVILIAN,
)
    db.add(user)
    await db.flush()
    return TokenResponse(access_token=create_access_token(user.id, {"role": user.role.value}), refresh_token=create_refresh_token(user.id), expires_in=86400)

@router.post("/anonymous", response_model=TokenResponse, status_code=201)
async def anonymous_token(db: AsyncSession = Depends(get_db)):
    user = User(is_anonymous=True, role=UserRole.CIVILIAN, display_name=f"Anon-{str(uuid.uuid4())[:8].upper()}")
    db.add(user)
    await db.flush()
    return TokenResponse(access_token=create_access_token(user.id, {"role": "civilian", "anon": True}), refresh_token=create_refresh_token(user.id), expires_in=86400)

@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    user.last_seen = datetime.now(timezone.utc)
    return TokenResponse(access_token=create_access_token(user.id, {"role": user.role.value}), refresh_token=create_refresh_token(user.id), expires_in=86400)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    return TokenResponse(access_token=create_access_token(user.id, {"role": user.role.value}), refresh_token=create_refresh_token(user.id), expires_in=86400)

@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: User = Depends(get_required_user)):
    return user

@router.patch("/me", response_model=UserProfileResponse)
async def update_me(body: UserUpdateRequest, user: User = Depends(get_required_user), db: AsyncSession = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.add(user)
    return user
