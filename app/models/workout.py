from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class WorkoutEntry:
    id: int | None
    user_id: int
    name: str
    duration_minutes: int | None
    calories_burned: int | None
    notes: str | None
    performed_at: datetime
