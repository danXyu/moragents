import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from models import get_db
from pydantic import BaseModel
from services.auth.wallet_auth import UserService, WalletAuthService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])

wallet_auth_service = WalletAuthService()

# In-memory token store (use Redis in production)
# Format: {token: wallet_address}
active_tokens = {}


# Request/Response models
class ChallengeRequest(BaseModel):
    wallet_address: str


class ChallengeResponse(BaseModel):
    challenge: str


class VerifyRequest(BaseModel):
    wallet_address: str
    signature: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int


@router.post("/challenge", response_model=ChallengeResponse)
def get_auth_challenge(request: ChallengeRequest):
    """Generate a challenge for the user to sign with their wallet"""
    challenge = wallet_auth_service.generate_challenge(request.wallet_address)
    return ChallengeResponse(challenge=challenge)


@router.post("/verify", response_model=AuthResponse)
def verify_wallet_signature(request: VerifyRequest, db: Session = Depends(get_db)):
    """Verify wallet signature and issue auth token"""
    valid = wallet_auth_service.verify_signature(request.wallet_address, request.signature)

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Get or create user
    user_service = UserService(db)
    user = user_service.get_or_create_user(request.wallet_address)

    # Generate simple bearer token
    token = secrets.token_hex(32)

    # Store token in memory (use Redis in production)
    active_tokens[token] = user.wallet_address

    return AuthResponse(access_token=token, token_type="bearer", user_id=user.id)


# Getting the current authenticated user
def get_current_wallet_address(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate bearer token from authorization header"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")

    token = parts[1]

    if token not in active_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return active_tokens[token]


# Dependency to get the current user
def get_current_user(wallet_address: str = Depends(get_current_wallet_address), db: Session = Depends(get_db)):
    """Get the current user from the wallet address"""
    user_service = UserService(db)
    user = user_service.get_user_by_wallet(wallet_address)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


@router.get("/me")
def get_current_user_profile(user=Depends(get_current_user)):
    """Get the current user profile"""
    return user.to_service_model()


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate the token"""
    if not authorization:
        return {"detail": "Already logged out"}

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return {"detail": "Invalid authorization format"}

    token = parts[1]

    if token in active_tokens:
        del active_tokens[token]

    return {"detail": "Successfully logged out"}
