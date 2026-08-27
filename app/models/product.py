from dataclasses import dataclass


@dataclass(slots=True)
class Product:
    id: int | None
    user_id: int
    name: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
