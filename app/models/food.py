from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FoodEntry:
    id: int | None
    user_id: int
    meal: str
    product_name: str
    quantity: float
    unit: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    eaten_at: datetime
