from dotenv import load_dotenv
import os

load_dotenv()

from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from pydantic import BaseModel, ConfigDict, Field
from database import engine, Base, SessionLocal
import models
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from jose import JWTError, jwt
from datetime import date, datetime, timezone, timedelta
from ai_service import generate_ai_recommendation

app = FastAPI()

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db=Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(models.User).filter(
        models.User.id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    return user
    
class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=12, max_length=72)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db)
):
    db_user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not pwd_context.verify(
        form_data.password, 
        db_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    
    token_data = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
    }

    token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/users")
def create_user(user: UserCreate, db=Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    password_hash = pwd_context.hash(user.password)

    db_user = models.User(
        username=user.username,
        password_hash=password_hash
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "id": db_user.id,
        "username": db_user.username
    }

class Workout(BaseModel):
    exercise: str
    sets: int
    reps: int
    weight: float
    workout_date: date | None = None

class WorkoutResponse(BaseModel):
    id: int
    exercise: str
    sets: int
    reps: int
    weight: float
    workout_date: date
    user_id: int
    created_at: datetime
    volume: float

    model_config = ConfigDict(from_attributes=True)

@app.get("/")
def home():
    return {"message": "AI Fitness Tracker API is running!"}

@app.get("/workouts", response_model=list[WorkoutResponse])
def get_all_workouts(
    exercise: str | None = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    )

    if exercise:
        query = query.filter(
            models.Workout.exercise.ilike(exercise)
        )

    workouts = query.order_by(
       models.Workout.created_at.desc()
    ).all()

    return [
        {
           "id": workout.id,
           "exercise": workout.exercise,
           "sets": workout.sets,
           "reps": workout.reps,
           "weight": workout.weight,
           "workout_date": workout.workout_date,
           "user_id": workout.user_id,
           "created_at": workout.created_at,
           "volume": workout.sets * workout.reps * workout.weight
        }
        for workout in workouts
    ]

@app.get("/workouts/history", response_model=list[WorkoutResponse])
def workout_history(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).all()

    return [
            {
               "id": workout.id,
               "exercise": workout.exercise,
               "sets": workout.sets,
               "reps": workout.reps,
               "weight": workout.weight,
               "workout_date": workout.workout_date,
               "user_id": workout.user_id,
               "created_at": workout.created_at,
               "volume": workout.sets * workout.reps * workout.weight
            }
            for workout in workouts
        ]

@app.get("/workouts/pr/{exercise}")
def get_personal_record(
    exercise: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workout = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id,
        models.Workout.exercise.ilike(exercise)
    ).order_by(
        models.Workout.weight.desc()
    ).first()

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="No workouts found for this exercise"
        )

    return {
        "exercise": workout.exercise,
        "weight": workout.weight,
        "sets": workout.sets,
        "reps": workout.reps,
        "workout_id": workout.id,
        "achieved_at": workout.created_at
    }

@app.get("/workouts/progress/{exercise}")
def get_progress(
    exercise: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id,
        models.Workout.exercise.ilike(exercise)
    ).order_by(
        models.Workout.created_at.asc()
    ).all()

    if not workouts:
        raise HTTPException(
            status_code=404,
            detail="No workouts found for this exercise"
        )

    first_workout = workouts[0]
    latest_workout = workouts[-1]

    return {
        "exercise": latest_workout.exercise,
        "first_weight": first_workout.weight,
        "latest_weight": latest_workout.weight,
        "first_workout_id": first_workout.id,
        "latest_workout_id": latest_workout.id
    }

@app.get("/workouts/volume/{excercise}")
def get_workout_volume(
    exercise: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id,
        models.Workout.exercise.ilike(exercise)
    ).all()

    if not workouts:
        raise HTTPException(
            status_code=404,
            detail="No workouts found for this exercise"
        )

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    return {
        "exercise": exercise,
        "total_volume": total_volume,
        "workout_count": len(workouts)
    }

@app.get("/workout/analytics/weekly")
def get_weekly_analytics(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id,
        models.Workout.created_at >= week_ago
    ).all()

    total_sets = sum(workout.sets for workout in workouts)
    total_reps = sum(workout.reps for workout in workouts)

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    exercise_counts = {}

    for workout in workouts:
        exercise_counts[workout.exercise] = (
            exercise_counts.get(workout.exercise, 0) + workout.sets
        )

    most_trained_exercise = (
        max(exercise_counts, key=exercise_counts.get)
        if exercise_counts
        else None
    )

    return {
        "workout_count": len(workouts),
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume": total_volume,
        "most_trained_exercise": most_trained_exercise
    }

@app.get("/ai/recommendation")
def get_ai_recommendation(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).limit(10).all()

    if not workouts:
        return {
            "recommendation": "Not enough workout data yet."
        }

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    return {
        "workout_count": len(workouts),
        "total_volume": total_volume,
        "recommendation": "Your workout data has been collected. AI analysis will be added next"
    }

@app.get("/ai/test")
def test_ai():
    response = client.responses.create(
        model="gpt-5-mini",
        input="Say hello in one short sentence."
    )

    return {
        "response": response.output_text
    }

@app.get("/ai/summary")
def get_ai_summary(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).limit(10).all()

    if not workouts:
        return {
            "message": "Not enough workout data."
        }

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    total_sets = sum(
        workout.sets for workout in workouts
    )

    total_reps = sum(
        workout.reps for workout in workouts
    )

    workout_data = []

    for workout in workouts:
        workout_data.append({
            "exercise": workout.exercise,
            "sets": workout.sets,
            "reps": workout.reps,
            "weight": workout.weight,
            "volume": workout.sets * workout.reps * workout.weight,
            "date": workout.created_at
        })

    return {
        "workout": workout_data,
        "workout_count": len(workouts),
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume": total_volume
    }

@app.get("/ai/prompt")
def get_ai_prompt(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).limit(10).all()

    if not workouts:
        return {
            "message": "Not enough workout data to analyze."
        }

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    workout_lines = []

    for workout in workouts:
        workout_lines.append(
            f"- {workout.exercise}: "
            f"{workout.sets} sets x "
            f"{workout.reps} reps @ "
            f"{workout.weight} lbs"
        )

    workout_text = "\n".join(workout_lines)

    prompt = f"""
You are an AI fitness coach.

Analyze the athlete's recent workout data.

Recent Workouts:
{workout_text}

Total workouts: {len(workouts)}
Total training volume: {total_volume} lbs

Provide:
1. A short assessment of the athlete's recent training.
2. One positive observation.
3. One recommendation for their next workout

Keep the response concise and practical
"""

    return {
        "prompt": prompt.strip()
    }

@app.get("/ai/recommendation/mock")
def mock_ai_recommendation(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).limit(10).all()

    if not workouts:
        return {
            "recommendation": "Not enough workout data yet."
        }

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    return {
    "analysis": "Your recent training shows consistent strength work.",
    "positive_observation": "You are completing structured sets with substantial training volume.",
    "recommendation": "Continue progressing gradually while maintaining good form and recovery.",
    "workout_count": len(workouts),
    "total_volume": total_volume
    
    }

@app.get("/ai/recommendation/real")
def real_ai_recommendation(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).order_by(
        models.Workout.created_at.desc()
    ).limit(10).all()

    if not workouts:
        return {
            "recommendation": "Not enough workout data yet."
        }

    total_volume = sum(
        workout.sets * workout.reps * workout.weight
        for workout in workouts
    )

    workout_lines = []

    for workout in workouts:
        workout_lines.append(
            f"- {workout.exercise}: "
            f"{workout.sets} sets x "
            f"{workout.reps} reps @ "
            f"{workout.weight} lbs"
        )

    workout_text = "\n".join(workout_lines)

    prompt = f"""
You are an AI fitness coach.

Analyze this athlete's recent workout data.

Recent workouts:
{workout_text}

Total workouts: {len(workouts)}
Total training volume: {total_volume} lbs

Provide:
1. A short assessment.
2. One positive observation.
3. One recommendation for the next workout.

Keep the response concise and practical.
"""

    recommendation = generate_ai_recommendation(prompt)

    return {
        "recommendation": recommendation
    }
    
@app.get("/workouts/{workout_id}")
def get_workouts(
    workout_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()

    if not workout:
        raise HTTPException(
            status_code=404,
            detail="Workout not found or does not belong to this user"
        )

    return workout

@app.post("/workouts")
def create_workout(
    workout: Workout,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_workout = models.Workout(
        exercise=workout.exercise,
        sets=workout.sets,
        reps=workout.reps,
        weight=workout.weight,
        workout_date=workout.workout_date or date.today(),
        user_id=current_user.id
    )

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)

    return db_workout

@app.delete("/workouts/{workout_id}")
def delete_workout(
    workout_id: int, 
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id 
    ).first()

    if workout is None:
        raise HTTPException(
            status_code=404, 
            detail="Workout not found or does not belong to this user"
        )

    db.delete(workout)
    db.commit()

    return {"message": "Workout deleted successfully"}

@app.put("/workouts/{workout_id}")
def update_workout(
    workout_id: int,
    workout: Workout,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()

    if db_workout is None:
        raise HTTPException(
            status_code=404, 
            detail="Workout not found"
        )

    db_workout.exercise = workout.exercise
    db_workout.sets = workout.sets
    db_workout.reps = workout.reps
    db_workout.weight = workout.weight
    db_workout.workout_date = (
        workout.workout_date or db_workout.workout_date
    )

    db.commit()
    db.refresh(db_workout)

    return db_workout