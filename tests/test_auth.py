
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base
from main import app, get_db


# Create an isolated, temporary test database.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_register_user():
    response = client.post(
        "/users",
        json={"username": "testuser", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_duplicate_username_is_rejected():
    client.post(
        "/users",
        json={"username": "testuser", "password": "StrongPass123"},
    )

    response = client.post(
        "/users",
        json={"username": "testuser", "password": "AnotherPass123"},
    )

    assert response.status_code == 409


def test_login_with_wrong_password_is_rejected():
    client.post(
        "/users",
        json={"username": "testuser", "password": "StrongPass123"},
    )

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_login_with_correct_password_succeeds():
    client.post(
        "/users",
        json={"username": "testuser", "password": "StrongPass123"},
    )

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
