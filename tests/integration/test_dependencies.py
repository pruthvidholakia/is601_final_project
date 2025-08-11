# tests/integration/test_dependencies.py
import pytest
from unittest.mock import patch
from fastapi import HTTPException, status
from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User
from uuid import uuid4
from datetime import datetime, timezone
from app.database import SessionLocal

# Sample user data dictionaries for testing
sample_user_data = {
    "id": uuid4(),
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

inactive_user_data = {
    "id": uuid4(),
    "username": "inactiveuser",
    "email": "inactive@example.com",
    "first_name": "Inactive",
    "last_name": "User",
    "is_active": False,
    "is_verified": False,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

# --- helpers ---
def _seed_user(db, data):
    # Idempotent: return if already exists (by id or username)
    existing = db.query(User).filter(
        (User.id == data["id"]) | (User.username == data["username"])
    ).first()
    if existing:
        return existing

    u = User(
        id=data["id"],
        username=data["username"],
        email=data["email"],
        password="dummyhash",  # satisfy NOT NULL
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        is_active=data.get("is_active", True),
        is_verified=data.get("is_verified", False),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def _naive(dt):
    return dt.replace(tzinfo=None) if dt and getattr(dt, "tzinfo", None) else dt

# Fixture for mocking token verification
@pytest.fixture
def mock_verify_token():
    with patch.object(User, 'verify_token') as mock:
        yield mock

# Test get_current_user with valid token and complete payload
# ----- tests -----
def test_get_current_user_valid_token_existing_user(mock_verify_token):
    mock_verify_token.return_value = sample_user_data
    with SessionLocal() as db:
        _seed_user(db, sample_user_data)
        user_response = get_current_user(token="validtoken", db=db)

    assert isinstance(user_response, UserResponse)
    assert user_response.id == sample_user_data["id"]
    assert user_response.username == sample_user_data["username"]
    assert user_response.email == sample_user_data["email"]
    assert user_response.first_name == sample_user_data["first_name"]
    assert user_response.last_name == sample_user_data["last_name"]
    assert user_response.is_active == sample_user_data["is_active"]
    assert user_response.is_verified == sample_user_data["is_verified"]
    # normalize tz for comparison
    assert _naive(user_response.created_at) == _naive(sample_user_data["created_at"])
    assert _naive(user_response.updated_at) == _naive(sample_user_data["updated_at"])

# Test get_current_user with invalid token (returns None)
def test_get_current_user_invalid_token(mock_verify_token):
    mock_verify_token.return_value = None
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalidtoken", db=db)
            
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    mock_verify_token.assert_called_once_with("invalidtoken")

# Test get_current_user with valid token but incomplete payload (simulate missing fields)
def test_get_current_user_valid_token_incomplete_payload(mock_verify_token):
    mock_verify_token.return_value = {}
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="validtoken", db=db)
            
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    mock_verify_token.assert_called_once_with("validtoken")

# Test get_current_active_user with an active user
def test_get_current_active_user_active(mock_verify_token):
    mock_verify_token.return_value = sample_user_data
    with SessionLocal() as db:
        _seed_user(db, sample_user_data)
        current_user = get_current_user(token="validtoken", db=db)
        active_user = get_current_active_user(current_user=current_user)
        assert isinstance(active_user, UserResponse)
        assert active_user.is_active is True

# Test get_current_active_user with an inactive user
def test_get_current_active_user_inactive(mock_verify_token):
    mock_verify_token.return_value = inactive_user_data
    with SessionLocal() as db:
        _seed_user(db, inactive_user_data)
        # get_current_user itself raises 400 for inactive users in your implementation
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="validtoken", db=db)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
