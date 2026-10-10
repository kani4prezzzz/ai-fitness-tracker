
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


def test_users_cannot_access_each_others_workouts():
    # Register two separate users.
    client.post(
        "/users",
        json={"username": "alice", "password": "StrongPass123"},
    )
    client.post(
        "/users",
        json={"username": "bob", "password": "StrongPass123"},
    )

    # Log in as Alice and Bob.
    alice_login = client.post(
        "/login",
        data={"username": "alice", "password": "StrongPass123"},
    )
    bob_login = client.post(
        "/login",
        data={"username": "bob", "password": "StrongPass123"},
    )

    alice_token = alice_login.json()["access_token"]
    bob_token = bob_login.json()["access_token"]

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Alice creates a workout.
    workout_response = client.post(
        "/workouts",
        json={
            "exercise": "Sprint",
            "sets": 4,
            "reps": 6,
            "weight": 100,
        },
        headers=alice_headers,
    )
    assert workout_response.status_code == 200
    workout_id = workout_response.json()["id"]

    # Bob cannot read Alice's workout.
    read_response = client.get(
        f"/workouts/{workout_id}",
        headers=bob_headers,
    )
    assert read_response.status_code == 404

    # Bob cannot edit Alice's workout.
    edit_response = client.put(
        f"/workouts/{workout_id}",
        json={
            "exercise": "Changed Exercise",
            "sets": 3,
            "reps": 5,
            "weight": 50,
        },
        headers=bob_headers,
    )
    assert edit_response.status_code == 404

    # Bob cannot delete Alice's workout.
    delete_response = client.delete(
        f"/workouts/{workout_id}",
        headers=bob_headers,
    )
    assert delete_response.status_code == 404

    # Confirm Alice's original workout still exists.
    owner_response = client.get(
        f"/workouts/{workout_id}",
        headers=alice_headers,
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["exercise"] == "Sprint"
