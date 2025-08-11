#app/auth/dependencies.py

from datetime import datetime
from uuid import UUID
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def _credentials_exc() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _user_to_response(user: User) -> UserResponse:
    """Map ORM user to API schema."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=getattr(user, "is_verified", False),
        created_at=getattr(user, "created_at", datetime.utcnow()),
        updated_at=getattr(user, "updated_at", datetime.utcnow()),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Decode JWT and return the *real* user from the database.
    - If the token contains a minimal payload (only 'sub'), we look up by id (preferred) or username/email.
    - If the token contains a full payload (username/email), we still fetch from DB to avoid stale data.
    - Never return a placeholder 'Unknown' user. If not found, raise 401.
    """
    token_data = User.verify_token(token)
    if token_data is None:
        raise _credentials_exc()

    user_obj: Optional[User] = None

    # Case 1: token_data is a dict
    if isinstance(token_data, dict): # pragma: no cover
        # Prefer id from 'sub' if present
        sub = token_data.get("sub")
        if sub:
            # sub might be a UUID string, UUID, username, or email depending on how you minted tokens
            # Try id first
            try:
                user_obj = db.query(User).filter(User.id == UUID(str(sub))).first()
            except Exception:
                user_obj = None

            # If not found by id, try username/email
            if not user_obj:
                user_obj = (
                    db.query(User)
                    .filter((User.username == str(sub)) | (User.email == str(sub)))
                    .first()
                )

        # If the token has explicit username/email, verify against DB to avoid stale info
        if not user_obj:
            uname = token_data.get("username")
            email = token_data.get("email")
            if uname:
                user_obj = db.query(User).filter(User.username == uname).first()
            if not user_obj and email:
                user_obj = db.query(User).filter(User.email == email).first() 

    # Case 2: token_data is a bare UUID
    elif isinstance(token_data, UUID): # pragma: no cover
        user_obj = db.query(User).filter(User.id == token_data).first()

    # If still not found -> invalid credentials
    if not user_obj:
        raise _credentials_exc()

    if not user_obj.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return _user_to_response(user_obj)


def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Ensure the user is active (kept for compatibility with your existing endpoints)."""
    if not current_user.is_active: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
