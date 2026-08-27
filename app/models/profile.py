from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserProfile:
    user_id: int
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    calories: int
    protein: int
    fat: int
    carbohydrates: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
