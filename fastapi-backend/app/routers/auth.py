import httpx

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    RefreshResponse,
)

from app.schemas.user import UserResponse
from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user_data.password
    )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role="customer"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        user_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    refresh_token = create_refresh_token(
        user_id=user.id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post(
    "/refresh",
    response_model=RefreshResponse
)
def refresh_token(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


# ============================================================
# AUTH0 LOGIN
# ============================================================

@router.get("/auth0/login")
def auth0_login():

    params = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
    }

    auth_url = (
        f"https://{settings.AUTH0_DOMAIN}/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(
        url=auth_url
    )


# ============================================================
# AUTH0 CALLBACK
# ============================================================

@router.get("/auth0/callback")
async def auth0_callback(
    code: str
):
    token_url = (
        f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    )

    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=payload
            )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to connect to Auth0: {str(exc)}"
        )

    if response.status_code != 200:
        try:
            auth0_response = response.json()
        except Exception:
            auth0_response = response.text

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Auth0 token exchange failed",
                "auth0_response": auth0_response
            }
        )

    return response.json()