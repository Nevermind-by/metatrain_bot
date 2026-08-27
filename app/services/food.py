from datetime import datetime, timezone

from app.models.food import FoodEntry
from app.repositories.food import FoodRepository


MEALS = {
    "breakfast": "Завтрак",
    "lunch": "Обед",
    "dinner": "Ужин",
    "snack": "Перекус",
}


class FoodService:
    def __init__(self, repository: FoodRepository | None = None) -> None:
        self.repository = repository or FoodRepository()

    async def add_entry(
        self,
        *,
        user_id: int,
        meal: str,
        product_name: str,
        grams: float,
        calories_per_100: float,
        protein_per_100: float,
        fat_per_100: float,
        carbohydrates_per_100: float,
    ) -> FoodEntry:
        if meal not in MEALS:
            raise ValueError("Unsupported meal")
        if grams <= 0:
            raise ValueError("Weight must be positive")

        ratio = grams / 100
        return await self.repository.create(
            FoodEntry(
                id=None,
                user_id=user_id,
                meal=meal,
                product_name=product_name.strip(),
                grams=grams,
                calories=round(calories_per_100 * ratio, 1),
                protein=round(protein_per_100 * ratio, 1),
                fat=round(fat_per_100 * ratio, 1),
                carbohydrates=round(carbohydrates_per_100 * ratio, 1),
                eaten_at=datetime.now(timezone.utc),
            )
        )

    async def today(self, user_id: int) -> list[FoodEntry]:
        day = datetime.now(timezone.utc).date().isoformat()
        return await self.repository.list_for_day(user_id, day)

    async def delete(self, user_id: int, entry_id: int) -> bool:
        return await self.repository.delete(user_id, entry_id)

    @staticmethod
    def totals(entries: list[FoodEntry]) -> dict[str, float]:
        return {
            "calories": round(sum(e.calories for e in entries), 1),
            "protein": round(sum(e.protein for e in entries), 1),
            "fat": round(sum(e.fat for e in entries), 1),
            "carbohydrates": round(sum(e.carbohydrates for e in entries), 1),
        }
