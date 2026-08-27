from app.database.connection import get_connection
from app.models.product import Product


class ProductRepository:
    async def create(self, product: Product) -> Product:
        async with await get_connection() as connection:
            await connection.execute(
                """INSERT INTO products (user_id, name, calories, protein, fat, carbohydrates)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET
                    calories=excluded.calories, protein=excluded.protein,
                    fat=excluded.fat, carbohydrates=excluded.carbohydrates""",
                (product.user_id, product.name, product.calories, product.protein, product.fat, product.carbohydrates),
            )
            await connection.commit()
            cursor = await connection.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (product.user_id, product.name))
            row = await cursor.fetchone()
        return self._to_model(row)

    async def search(self, user_id: int, query: str, limit: int = 10) -> list[Product]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM products WHERE user_id = ? AND name LIKE ? ORDER BY name LIMIT ?", (user_id, f"%{query.strip()}%", limit))
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def list_recent(self, user_id: int, limit: int = 10) -> list[Product]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM products WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def get(self, user_id: int, product_id: int) -> Product | None:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
            row = await cursor.fetchone()
        return self._to_model(row) if row else None

    @staticmethod
    def _to_model(row) -> Product:
        return Product(id=row["id"], user_id=row["user_id"], name=row["name"], calories=row["calories"], protein=row["protein"], fat=row["fat"], carbohydrates=row["carbohydrates"])
