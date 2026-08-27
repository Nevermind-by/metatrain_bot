from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class WorkoutSet:
    id: int | None
    exercise_id: int
    set_number: int
    weight_kg: float
    reps: int
    rpe: float | None = None


@dataclass(slots=True)
class WorkoutExercise:
    id: int | None
    workout_id: int
    name: str
    position: int
    sets: list[WorkoutSet] = field(default_factory=list)


@dataclass(slots=True)
class WorkoutEntry:
    id: int | None
    user_id: int
    name: str
    duration_minutes: int | None
    calories_burned: int | None
    notes: str | None
    performed_at: datetime
