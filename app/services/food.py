from datetime import datetime, timezone

from app.models.food import FoodEntry
from app.repositories.food import FoodRepository


MEALS = {"breakfast": "Завтрак", "lunch": "Обед", "dinner": "Ужин", "snack": "Перекус"}


class FoodService:
    def __init__(self, repository: FoodRepository | None = None) -> None:
        self.repository = repository or FoodRepository()

    async def add_product_entry(self, *, user_id: int, meal: str, product_name: str, grams: float,
                                calories_per_100: float, protein_per_100: float, fat_per_100: float,
                                carbohydrates_per_100: float) -> FoodEntry:
        if meal not in MEALS or grams <= 0:
            raise ValueError("Invalid food entry")
        ratio = grams / 100
        return await self.repository.create(FoodEntry(
            id=None, user_id=user_id, meal=meal, product_name=product_name.strip(), quantity=grams, unit="g",
            calories=round(calories_per_100 * ratio, 1), protein=round(protein_per_100 * ratio, 1),
            fat=round(fat_per_100 * ratio, 1), carbohydrates=round(carbohydrates_per_100 * ratio, 1),
            eaten_at=datetime.now(timezone.utc)))

    async def add_recipe_entry(self, *, user_id: int, meal: str, recipe_name: str, servings: float,
                               calories_per_serving: float, protein_per_serving: float,
                               fat_per_serving: float, carbohydrates_per_serving: float) -> FoodEntry:
        if meal not in MEALS or servings <= 0:
            raise ValueError("Invalid recipe entry")
        return await self.repository.create(FoodEntry(
            id=None, user_id=user_id, meal=meal, product_name=recipe_name.strip(), quantity=servings, unit="portion",
            calories=round(calories_per_serving * servings, 1), protein=round(protein_per_serving * servings, 1),
            fat=round(fat_per_serving * servings, 1), carbohydrates=round(carbohydrates_per_serving * servings, 1),
            eaten_at=datetime.now(timezone.utc)))

    async def today(self, user_id: int) -> list[FoodEntry]:
        return await self.repository.list_for_day(user_id, datetime.now(timezone.utc).date().isoformat())

    async def history(self, user_id: int, days: int = 7) -> list[FoodEntry]:
        return await self.repository.list_since(user_id, days)

    async def delete(self, user_id: int, entry_id: int) -> bool:
        return await self.repository.delete(user_id, entry_id)

    @staticmethod
    def totals(entries: list[FoodEntry]) -> dict[str, float]:
        return {k: round(sum(getattr(e, k) for e in entries), 1) for k in ("calories", "protein", "fat", "carbohydrates")}

    @staticmethod
    def average_daily_calories(entries: list[FoodEntry], days: int) -> float:
        if days <= 0:
            raise ValueError("Days must be positive")
        return round(sum(e.calories for e in entries) / days, 1)
