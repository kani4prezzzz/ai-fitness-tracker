from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date, UniqueConstraint
from datetime import date, datetime, timezone 
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exercise: Mapped[str] = mapped_column(String(100))
    sets: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)

    workout_date: Mapped[date] = mapped_column(
    Date,
    default=lambda: datetime.now(timezone.utc).date(),
    nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), 
        nullable=False
    )
    user: Mapped["User"] = relationship(
        back_populates="workouts"
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="athlete",
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    weekly_goal: Mapped[int] = mapped_column(
    Integer,
    default=4,
    nullable=False
    )

    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user"
    )

    teams: Mapped[list["Team"]] = relationship(
        back_populates="coach"
    )

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    coach: Mapped["User"] = relationship(
        back_populates="teams"
    )

class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "team_id"),
    )

class TeamWorkout(Base):
    __tablename__ = "team_workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False
    )

    exercise: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    sets: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    reps: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    target_weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )   

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class WorkoutCompletion(Base):
    __tablename__ = "workout_completions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    team_workout_id: Mapped[int] = mapped_column(
        ForeignKey("team_workouts.id"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    completed_sets: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    completed_reps: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    actual_weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )