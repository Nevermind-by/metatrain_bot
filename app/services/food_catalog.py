from app.models.food_catalog import FoodCatalogItem
from app.repositories.food_catalog import FoodCatalogRepository


class FoodCatalogService:
    def __init__(self, repository: FoodCatalogRepository | None = None) -> None:
        self.repository = repository or FoodCatalogRepository()

    async def search(self, query: str, limit: int = 20) -> list[FoodCatalogItem]:
        return await self.repository.search(query, limit)

    async def get(self, food_id: int) -> FoodCatalogItem | None:
        return await self.repository.get(food_id)

    @staticmethod
    def calculate(item: FoodCatalogItem, grams: float) -> dict[str, float]:
        if grams <= 0:
            raise ValueError("Quantity must be positive")
        ratio = grams / 100
        return {
            "calories": round(item.calories_per_100g * ratio, 1),
            "protein": round(item.protein_per_100g * ratio, 1),
            "fat": round(item.fat_per_100g * ratio, 1),
            "carbohydrates": round(item.carbohydrates_per_100g * ratio, 1),
            "fiber": round(item.fiber_per_100g * ratio, 1) if item.fiber_per_100g is not None else None,
        }
