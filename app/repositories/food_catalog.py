from app.database.connection import get_connection
from app.models.food_catalog import FoodCatalogItem


class FoodCatalogRepository:
    async def search(self, query: str, limit: int = 20) -> list[FoodCatalogItem]:
        normalized = " ".join(query.casefold().split()).strip()
        if not normalized:
            return []
        pattern = f"%{normalized}%"
        async with await get_connection() as connection:
            cursor = await connection.execute(
                """SELECT f.* FROM food_catalog f
                WHERE f.normalized_name LIKE ?
                   OR EXISTS (
                       SELECT 1 FROM food_aliases a
                       WHERE a.food_id = f.id AND a.normalized_alias LIKE ?
                   )
                ORDER BY CASE WHEN f.normalized_name = ? THEN 0
                              WHEN f.normalized_name LIKE ? THEN 1 ELSE 2 END,
                         length(f.name), f.name
                LIMIT ?""",
                (pattern, pattern, normalized, f"{normalized}%", limit),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def get(self, food_id: int) -> FoodCatalogItem | None:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM food_catalog WHERE id = ?", (food_id,))
            row = await cursor.fetchone()
        return self._to_model(row) if row else None

    @staticmethod
    def _to_model(row) -> FoodCatalogItem:
        return FoodCatalogItem(
            id=row["id"], source=row["source"], source_id=row["source_id"],
            name=row["name"], normalized_name=row["normalized_name"],
            category=row["category"], brand=row["brand"], preparation=row["preparation"],
            calories_per_100g=row["calories_per_100g"], protein_per_100g=row["protein_per_100g"],
            fat_per_100g=row["fat_per_100g"], carbohydrates_per_100g=row["carbohydrates_per_100g"],
            fiber_per_100g=row["fiber_per_100g"],
        )
