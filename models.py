from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Date
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

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user"
    )