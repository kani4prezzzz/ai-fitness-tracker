
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone

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

def test_workout_history_only_shows_current_users_workouts():
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

    # Each user creates a workout.
    client.post(
        "/workouts",
        json={
            "exercise": "Alice Sprint",
            "sets": 4,
            "reps": 6,
            "weight": 100,
        },
        headers=alice_headers,
    )

    client.post(
        "/workouts",
        json={
            "exercise": "Bob Squat",
            "sets": 3,
            "reps": 8,
            "weight": 150,
        },
        headers=bob_headers,
    )

    # Retrieve each user's workout history.
    alice_history = client.get(
        "/workouts/history",
        headers=alice_headers,
    )
    bob_history = client.get(
        "/workouts/history",
        headers=bob_headers,
    )

    # Verify each user sees only their own workout.
    assert alice_history.status_code == 200
    assert [w["exercise"] for w in alice_history.json()] == ["Alice Sprint"]

    assert bob_history.status_code == 200
    assert [w["exercise"] for w in bob_history.json()] == ["Bob Squat"]

def test_weekly_analytics_only_counts_current_users_workouts():
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

    alice_headers = {
        "Authorization": f"Bearer {alice_login.json()['access_token']}"
    }
    bob_headers = {
        "Authorization": f"Bearer {bob_login.json()['access_token']}"
    }

    # Each user creates a workout.
    client.post(
        "/workouts",
        json={
            "exercise": "Alice Sprint",
            "sets": 4,
            "reps": 6,
            "weight": 100,
        },
        headers=alice_headers,
    )

    client.post(
        "/workouts",
        json={
            "exercise": "Bob Squat",
            "sets": 3,
            "reps": 8,
            "weight": 150,
        },
        headers=bob_headers,
    )

    # Request weekly analytics for each user.
    alice_response = client.get(
        "/workout/analytics/weekly",
        headers=alice_headers,
    )
    bob_response = client.get(
        "/workout/analytics/weekly",
        headers=bob_headers,
    )

    # Confirm Alice's statistics include only her workout.
    assert alice_response.status_code == 200
    assert alice_response.json()["workout_count"] == 1
    assert alice_response.json()["total_sets"] == 4
    assert alice_response.json()["total_reps"] == 6
    assert alice_response.json()["total_volume"] == 2400
    assert alice_response.json()["most_trained_exercise"] == "Alice Sprint"

    # Confirm Bob's statistics include only his workout.
    assert bob_response.status_code == 200
    assert bob_response.json()["workout_count"] == 1
    assert bob_response.json()["total_sets"] == 3
    assert bob_response.json()["total_reps"] == 8
    assert bob_response.json()["total_volume"] == 3600
    assert bob_response.json()["most_trained_exercise"] == "Bob Squat"

def test_user_can_update_weekly_goal():
    # Register a user.
    client.post(
        "/users",
        json={
            "username": "goaluser",
            "password": "StrongPass123",
        },
    )

    # Log in.
    login_response = client.post(
        "/login",
        data={
            "username": "goaluser",
            "password": "StrongPass123",
        },
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update the weekly goal to 5 days.
    response = client.put(
        "/goals/weekly",
        json={"weekly_goal": 5},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["weekly_goal"] == 5

def test_weekly_goal_rejects_invalid_value():
    # Register a user.
    client.post(
        "/users",
        json={
            "username": "invalidgoal",
            "password": "StrongPass123",
        },
    )

    # Log in.
    login_response = client.post(
        "/login",
        data={
            "username": "invalidgoal",
            "password": "StrongPass123",
        },
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to set a goal above the maximum of 7 days.
    response = client.put(
        "/goals/weekly",
        json={"weekly_goal": 8},
        headers=headers,
    )

    assert response.status_code == 422

def test_weekly_goal_counts_unique_workout_days():
    # Register a user.
    client.post(
        "/users",
        json={
            "username": "daycounter",
            "password": "StrongPass123",
        },
    )

    # Log in.
    login_response = client.post(
        "/login",
        data={
            "username": "daycounter",
            "password": "StrongPass123",
        },
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Calculate Monday and Tuesday of the current week.
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    tuesday = monday + timedelta(days=1)

    # Log two exercises on Monday.
    for exercise in ["Squat", "Bench Press"]:
        client.post(
            "/workouts",
            json={
                "exercise": exercise,
                "sets": 3,
                "reps": 10,
                "weight": 100,
                "workout_date": monday.isoformat(),
            },
            headers=headers,
        )

    # Log one exercise on Tuesday.
    client.post(
        "/workouts",
        json={
            "exercise": "Deadlift",
            "sets": 3,
            "reps": 5,
            "weight": 150,
            "workout_date": tuesday.isoformat(),
        },
        headers=headers,
    )

    # Check weekly progress.
    response = client.get(
        "/goals/weekly",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["completed_days"] == 2

def test_weekly_goal_progress_is_user_specific():
    # Register two users.
    for username in ["alice", "bob"]:
        client.post(
            "/users",
            json={
                "username": username,
                "password": "StrongPass123",
            },
        )

    # Log in as Alice.
    alice_login = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "StrongPass123",
        },
    )
    alice_token = alice_login.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    # Alice logs a workout.
    client.post(
        "/workouts",
        json={
            "exercise": "Squat",
            "sets": 3,
            "reps": 10,
            "weight": 100,
        },
        headers=alice_headers,
    )

    # Log in as Bob.
    bob_login = client.post(
        "/login",
        data={
            "username": "bob",
            "password": "StrongPass123",
        },
    )
    bob_token = bob_login.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Check each user's weekly progress.
    alice_progress = client.get(
        "/goals/weekly",
        headers=alice_headers,
    )
    bob_progress = client.get(
        "/goals/weekly",
        headers=bob_headers,
    )

    assert alice_progress.status_code == 200
    assert bob_progress.status_code == 200
    assert alice_progress.json()["completed_days"] == 1
    assert bob_progress.json()["completed_days"] == 0