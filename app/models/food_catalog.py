from dataclasses import dataclass


@dataclass(slots=True)
class FoodCatalogItem:
    id: int
    source: str
    source_id: str
    name: str
    normalized_name: str
    category: str | None
    brand: str | None
    preparation: str | None
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbohydrates_per_100g: float
    fiber_per_100g: float | None
