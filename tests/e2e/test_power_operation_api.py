import requests
from uuid import uuid4
import pytest

@pytest.fixture
def base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")

def _register_and_token(base_url: str):
    email = f"calc_{uuid4().hex[:8]}@example.com"
    username = f"calc_{uuid4().hex[:8]}"
    password = "SecurePass123!"
    r = requests.post(f"{base_url}/auth/register", json={
        "first_name": "Cal",
        "last_name": "Cuser",
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password
    })
    assert r.status_code == 201, r.text
    r2 = requests.post(f"{base_url}/auth/login", json={
        "username": username, "password": password
    })
    assert r2.status_code == 200, r2.text
    return {"Authorization": f"Bearer {r2.json()['access_token']}"}

def test_create_power_and_list(base_url: str):
    headers = _register_and_token(base_url)

    # Create power calc: 2 ** 3 = 8
    r = requests.post(f"{base_url}/calculations", json={
        "type": "power",
        "inputs": [2, 3]
    }, headers=headers)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["type"] == "power"
    assert created["result"] == 8
    calc_id = created["id"]

    # Should appear in list
    r_list = requests.get(f"{base_url}/calculations", headers=headers)
    assert r_list.status_code == 200
    ids = {item["id"] for item in r_list.json()}
    assert calc_id in ids

def test_power_requires_exactly_two_inputs(base_url: str):
    headers = _register_and_token(base_url)
    r = requests.post(f"{base_url}/calculations", json={
        "type": "power",
        "inputs": [2, 3, 4]  # invalid per schema validator
    }, headers=headers)
    # Pydantic validator triggers -> FastAPI 422
    assert r.status_code == 422, r.text
