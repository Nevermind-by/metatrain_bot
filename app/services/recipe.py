from app.models.recipe import Recipe, RecipeIngredient
from app.repositories.product import ProductRepository
from app.repositories.recipe import RecipeRepository


class RecipeService:
    def __init__(self, repository: RecipeRepository | None = None, product_repository: ProductRepository | None = None) -> None:
        self.repository = repository or RecipeRepository()
        self.product_repository = product_repository or ProductRepository()

    async def create(self, user_id: int, name: str, servings: int, items: list[tuple[int, float]]) -> Recipe:
        name = name.strip()
        if not name:
            raise ValueError("Название блюда не может быть пустым")
        if servings < 1:
            raise ValueError("Количество порций должно быть больше нуля")
        if not items:
            raise ValueError("Добавь хотя бы один продукт")

        totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbohydrates": 0.0}
        ingredients: list[RecipeIngredient] = []
        for product_id, grams in items:
            if grams <= 0:
                raise ValueError("Вес продукта должен быть больше нуля")
            product = await self.product_repository.get(user_id, product_id)
            if product is None:
                raise ValueError("Один из продуктов не найден")
            ratio = grams / 100
            for key in totals:
                totals[key] += getattr(product, key) * ratio
            ingredients.append(RecipeIngredient(None, 0, product_id, grams))

        recipe = Recipe(None, user_id, name, servings, *(round(totals[key], 1) for key in ("calories", "protein", "fat", "carbohydrates")))
        return await self.repository.create(recipe, ingredients)

    async def list(self, user_id: int) -> list[Recipe]:
        return await self.repository.list(user_id)
