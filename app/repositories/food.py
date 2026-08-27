from datetime import datetime, timedelta, timezone

from app.database.connection import get_connection
from app.models.food import FoodEntry


class FoodRepository:
    async def create(self, entry: FoodEntry) -> FoodEntry:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                """
                INSERT INTO food_entries (
                    user_id, meal, product_name, grams,
                    calories, protein, fat, carbohydrates, eaten_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.user_id, entry.meal, entry.product_name, entry.grams,
                    entry.calories, entry.protein, entry.fat,
                    entry.carbohydrates, entry.eaten_at.isoformat(),
                ),
            )
            await connection.commit()
            entry.id = cursor.lastrowid
        return entry

    async def list_for_day(self, user_id: int, day: str) -> list[FoodEntry]:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM food_entries WHERE user_id = ? AND date(eaten_at) = ? ORDER BY eaten_at",
                (user_id, day),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def list_since(self, user_id: int, days: int) -> list[FoodEntry]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM food_entries WHERE user_id = ? AND eaten_at >= ? ORDER BY eaten_at DESC",
                (user_id, since.isoformat()),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def delete(self, user_id: int, entry_id: int) -> bool:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "DELETE FROM food_entries WHERE id = ? AND user_id = ?",
                (entry_id, user_id),
            )
            await connection.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _to_model(row) -> FoodEntry:
        eaten_at = datetime.fromisoformat(row["eaten_at"])
        if eaten_at.tzinfo is None:
            eaten_at = eaten_at.replace(tzinfo=timezone.utc)
        return FoodEntry(
            id=row["id"], user_id=row["user_id"], meal=row["meal"],
            product_name=row["product_name"], grams=row["grams"],
            calories=row["calories"], protein=row["protein"],
            fat=row["fat"], carbohydrates=row["carbohydrates"],
            eaten_at=eaten_at,
        )
