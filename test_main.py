import pytest
from fastapi.testclient import TestClient
from main import app, get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///:memory:?cache=shared"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# User Tests
def test_create_user(test_db):
    response = client.post(
        "/users/",
        json={"name": "John Doe", "email": "john@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {"name": "John Doe", "email": "john@example.com"}

def test_get_user_not_found(test_db):
    response = client.get("/users/nonexistent@example.com")
    assert response.status_code == 404

def test_get_user_by_email(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    response = client.get("/users/john@example.com")
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"

def test_update_user(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    update_data = {"name": "John Updated", "email": "john@example.com"}
    response = client.put("/users/john@example.com", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "John Updated"

def test_delete_user(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    response = client.delete("/user/john@example.com")
    assert response.status_code == 200
    response = client.get("/users/john@example.com")
    assert response.status_code == 404

def test_create_duplicate_user(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    response = client.post("/users/", json={"name": "John", "email": "john@example.com"})
    assert response.status_code == 500

# House Tests
def test_create_house_valid_user(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    response = client.post(
        "/houses/",
        json={"address": "123 Main St", "user_email": "john@example.com"}
    )
    assert response.status_code == 200

def test_create_house_with_invalid_user(test_db):
    response = client.post(
        "/houses/",
        json={"address": "123 Main St", "user_email": "invalid@example.com"}
    )
    assert response.status_code == 404

def test_get_house_by_address(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    response = client.get("/houses/123 Main St")
    assert response.status_code == 200

def test_update_house_address(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    response = client.put(
        "/houses/123 Main St",
        json={"address": "456 Elm St", "user_email": "john@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["address"] == "456 Elm St"

def test_delete_house(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    response = client.delete("/houses/123 Main St")
    assert response.status_code == 200

# Room Tests
def test_create_room_valid_house(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    response = client.post("/rooms/", json={"name": "Living Room", "house_adrs": "123 Main St"})
    assert response.status_code == 200

def test_create_room_invalid_house(test_db):
    response = client.post("/rooms/", json={"name": "Living Room", "house_adrs": "invalid"})
    assert response.status_code == 404

def test_update_room_house(test_db):
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    client.post("/houses/", json={"address": "456 Elm St", "user_email": "john@example.com"})
    client.post("/rooms/", json={"name": "Living Room", "house_adrs": "123 Main St"})
    response = client.put(
        "/rooms/Living Room",
        json={"name": "Living Room", "house_adrs": "456 Elm St"}
    )
    assert response.status_code == 200

def test_delete_room(test_db):
    # Create required dependencies
    client.post("/users/", json={"name": "John", "email": "john@example.com"})
    client.post("/houses/", json={"address": "123 Main St", "user_email": "john@example.com"})
    client.post("/rooms/", json={"name": "Living Room", "house_adrs": "123 Main St"})

    # Delete the room
    delete_response = client.delete("/rooms/Living Room")
    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "name": "Living Room",
        "house_adrs": "123 Main St"
    }

    # Verify deletion
    get_response = client.get("/rooms/Living Room")
    assert get_response.status_code == 404

    # Verify house still exists
    house_response = client.get("/houses/123 Main St")
    assert house_response.status_code == 200