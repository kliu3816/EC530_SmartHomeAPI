import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Override the dependency to use test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

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

# House Tests
def test_create_house_with_invalid_user(test_db):
    response = client.post(
        "/houses/",
        json={"address": "123 Main St", "user_email": "invalid@example.com"}
    )
    assert response.status_code == 404

# Add similar tests for other endpoints (update/delete operations, etc.)