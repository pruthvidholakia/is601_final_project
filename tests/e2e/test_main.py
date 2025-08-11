import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as mainmod
from app.database import Base, get_db
from app.auth.dependencies import get_current_active_user

# Shared in-memory SQLite across threads/connections
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

# Patch the app's engine so lifespan create_all uses this engine too
mainmod.engine = engine

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

FIXED_USER_ID = uuid.uuid4()

class FakeUser:
    def __init__(self, id=None):
        self.id = id or FIXED_USER_ID
        self.is_active = True
        self.is_verified = True

def override_get_current_active_user():
    # Always return the same user id
    return FakeUser(FIXED_USER_ID)

mainmod.app.dependency_overrides[get_db] = override_get_db
mainmod.app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(mainmod.app)

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_calculations_crud_happy_path():
    # Create
    r = client.post("/calculations", json={"type": "addition", "inputs": [2, 3]})
    assert r.status_code == 201, r.text
    created = r.json()
    calc_id = created["id"]

    # List
    r = client.get("/calculations")
    assert r.status_code == 200
    assert any(c["id"] == calc_id for c in r.json())

    # Read
    r = client.get(f"/calculations/{calc_id}")
    assert r.status_code == 200
    assert r.json()["result"] == 5

    # Update
    r = client.put(f"/calculations/{calc_id}", json={"inputs": [10, 7]})
    assert r.status_code == 200
    assert r.json()["result"] == 17

    # Delete
    r = client.delete(f"/calculations/{calc_id}")
    assert r.status_code == 204

    # Not found after delete
    r = client.get(f"/calculations/{calc_id}")
    assert r.status_code == 404

def test_bad_uuid_and_404():
    r = client.get("/calculations/not-a-uuid")
    assert r.status_code == 400

    r = client.get(f"/calculations/{uuid.uuid4()}")
    assert r.status_code == 404
