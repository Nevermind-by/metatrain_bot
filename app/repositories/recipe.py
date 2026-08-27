from app.database.connection import get_connection
from app.models.recipe import Recipe, RecipeIngredient


class RecipeRepository:
    async def create(self, recipe: Recipe, ingredients: list[RecipeIngredient]) -> Recipe:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                """INSERT INTO recipes
                (user_id, name, servings, calories, protein, fat, carbohydrates)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (recipe.user_id, recipe.name, recipe.servings, recipe.calories,
                 recipe.protein, recipe.fat, recipe.carbohydrates),
            )
            recipe.id = cursor.lastrowid
            await connection.executemany(
                "INSERT INTO recipe_ingredients (recipe_id, product_id, grams) VALUES (?, ?, ?)",
                [(recipe.id, item.product_id, item.grams) for item in ingredients],
            )
            await connection.commit()
        return recipe

    async def list(self, user_id: int, limit: int = 50) -> list[Recipe]:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM recipes WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    async def get(self, user_id: int, recipe_id: int) -> Recipe | None:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM recipes WHERE id = ? AND user_id = ?",
                (recipe_id, user_id),
            )
            row = await cursor.fetchone()
        return self._to_model(row) if row else None

    @staticmethod
    def _to_model(row) -> Recipe:
        return Recipe(
            id=row["id"], user_id=row["user_id"], name=row["name"], servings=row["servings"],
            calories=row["calories"], protein=row["protein"], fat=row["fat"], carbohydrates=row["carbohydrates"],
        )
