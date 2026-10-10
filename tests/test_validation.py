
from pydantic import ValidationError

from main import UserCreate, Workout


def test_short_password_is_rejected():
    try:
        UserCreate(username="testuser", password="short")
        assert False, "Short password should be rejected"
    except ValidationError:
        pass


def test_invalid_workout_is_rejected():
    try:
        Workout(
            exercise="Sprint",
            sets=0,
            reps=6,
            weight=100
        )
        assert False, "Zero sets should be rejected"
    except ValidationError:
        pass


def test_valid_workout_is_accepted():
    workout = Workout(
        exercise="Sprint",
        sets=4,
        reps=6,
        weight=100
    )

    assert workout.exercise == "Sprint"
    assert workout.sets == 4
