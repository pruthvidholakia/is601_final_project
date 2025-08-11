import requests
from uuid import uuid4
import pytest

@pytest.fixture
def base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")

def _register(base_url: str):
    email = f"user_{uuid4().hex[:8]}@example.com"
    username = f"user_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    r = requests.post(f"{base_url}/auth/register", json={
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password
    })
    assert r.status_code == 201, r.text
    return email, username, password

def _login(base_url: str, username: str, password: str):
    r = requests.post(f"{base_url}/auth/login", json={
        "username": username,
        "password": password
    })
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"]

def test_profile_update_flow(base_url: str):
    email, username, password = _register(base_url)
    token = _login(base_url, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Before update
    r_me = requests.get(f"{base_url}/user/me", headers=headers)
    assert r_me.status_code == 200, r_me.text
    me = r_me.json()
    assert me["email"] == email
    assert me["username"] == username

    # Update profile
    new_username = f"updated_{uuid4().hex[:6]}"
    r_upd = requests.put(f"{base_url}/user/profile", json={
        "first_name": "Updated",
        "last_name": "Name",
        "username": new_username
    }, headers=headers)
    assert r_upd.status_code == 200, r_upd.text
    updated = r_upd.json()
    assert updated["first_name"] == "Updated"
    assert updated["last_name"] == "Name"
    assert updated["username"] == new_username
    assert updated["email"] == email  # unchanged

    # After update, /user/me reflects changes
    r_me2 = requests.get(f"{base_url}/user/me", headers=headers)
    assert r_me2.status_code == 200
    me2 = r_me2.json()
    assert me2["username"] == new_username
    assert me2["first_name"] == "Updated"
    assert me2["last_name"] == "Name"

def test_password_change_flow(base_url: str):
    _, username, old_pw = _register(base_url)
    token = _login(base_url, username, old_pw)
    headers = {"Authorization": f"Bearer {token}"}

    new_pw = "EvenStronger123!"
    r = requests.post(f"{base_url}/user/change-password", json={
        "current_password": old_pw,
        "new_password": new_pw,
        "confirm_new_password": new_pw
    }, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json().get("message") == "Password updated successfully"

    # Old password should fail
    r_old = requests.post(f"{base_url}/auth/login", json={
        "username": username, "password": old_pw
    })
    assert r_old.status_code == 401

    # New password should work
    r_new = requests.post(f"{base_url}/auth/login", json={
        "username": username, "password": new_pw
    })
    assert r_new.status_code == 200
    assert r_new.json().get("access_token")
