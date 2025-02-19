import pytest
from fastapi.testclient import TestClient
from main import app, get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        yield db
        db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_and_get_user():
    # Test user creation
    response = client.post(
        "/users/",
        json={"name": "John Doe", "email": "john@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"
    
    # Test get user
    response = client.get("/users/john@example.com")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"

def test_update_user():
    # Create user
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    
    # Update user
    response = client.put(
        "/users/john@example.com",
        json={"name": "John Updated"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Updated"

def test_delete_user():
    # Create user
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    
    # Delete user
    response = client.delete("/users/john@example.com")
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get("/users/john@example.com")
    assert response.status_code == 404

def test_create_duplicate_user():
    # First creation should succeed
    response = client.post(
        "/users/",
        json={"name": "John", "email": "john@example.com"}
    )
    assert response.status_code == 200
    
    # Second creation should fail
    response = client.post(
        "/users/",
        json={"name": "John", "email": "john@example.com"}
    )
    assert response.status_code == 400

def test_house_crud():
    # Create user
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    
    # Create house
    response = client.post(
        "/houses/",
        json={"address": "123 Main St", "user_email": "john@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["address"] == "123 Main St"
    
    # Get house
    response = client.get("/houses/123 Main St")
    assert response.status_code == 200
    
    # Update house
    response = client.put(
        "/houses/123 Main St",
        json={"address": "456 Elm St", "user_email": "john@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["address"] == "456 Elm St"
    
    # Delete house
    response = client.delete("/houses/456 Elm St")
    assert response.status_code == 200

def test_room_crud():
    # Create user and house
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    
    # Create room
    response = client.post(
        "/rooms/",
        json={"name": "Living Room", "house_adrs": "123 Main St"}
    )
    assert response.status_code == 200
    
    # Get room
    response = client.get("/rooms/Living Room")
    assert response.status_code == 200
    
    # Update room
    response = client.put(
        "/rooms/Living Room",
        json={"name": "Living Room", "house_adrs": "123 Main St"}
    )
    assert response.status_code == 200
    
    # Delete room
    response = client.delete("/rooms/Living Room")
    assert response.status_code == 200

def test_full_flow():
    # Create user
    client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
    
    # Create house
    client.post("/houses/", json={"address": "456 Oak Rd", "user_email": "alice@example.com"})
    
    # Create room
    client.post("/rooms/", json={"name": "Kitchen", "house_adrs": "456 Oak Rd"})
    
    # Create device
    response = client.post(
        "/devices/",
        json={"name": "Smart Light", "room_name": "Kitchen"}
    )
    assert response.status_code == 200
    
    # Verify device creation
    response = client.get("/devices/Smart Light")
    assert response.status_code == 200
    assert response.json()["room_name"] == "Kitchen"