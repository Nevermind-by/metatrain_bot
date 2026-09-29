from app.database.connection import get_connection
from app.models.food_catalog import FoodCatalogItem
from app.services.food_search import search_terms


class FoodCatalogRepository:
    async def search(self, query: str, limit: int = 20) -> list[FoodCatalogItem]:
        terms = search_terms(query)
        if not terms:
            return []

        conditions: list[str] = []
        params: list[object] = []
        for term in terms:
            pattern = f"%{term}%"
            conditions.append(
                "(f.normalized_name LIKE ? OR EXISTS ("
                "SELECT 1 FROM food_aliases a "
                "WHERE a.food_id = f.id AND a.normalized_alias LIKE ?))"
            )
            params.extend((pattern, pattern))

        # Rank the original query first, then translated terms.
        ranking_parts: list[str] = []
        for term in terms:
            ranking_parts.append(
                "CASE WHEN f.normalized_name = ? THEN 0 "
                "WHEN f.normalized_name LIKE ? THEN 1 ELSE 2 END"
            )
            params.extend((term, f"{term}%"))

        sql = f"""SELECT f.* FROM food_catalog f
        WHERE {' OR '.join(conditions)}
        ORDER BY {', '.join(ranking_parts)},
                 CASE WHEN f.brand IS NULL OR f.brand = '' THEN 0 ELSE 1 END,
                 length(f.name), f.name
        LIMIT ?"""
        params.append(limit)

        async with await get_connection() as connection:
            cursor = await connection.execute(sql, tuple(params))
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
