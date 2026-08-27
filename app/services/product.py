from app.models.product import Product
from app.repositories.product import ProductRepository


class ProductService:
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()

    async def create(self, *, user_id: int, name: str, calories: float, protein: float,
                     fat: float, carbohydrates: float) -> Product:
        name = name.strip()
        if not name:
            raise ValueError("Product name is required")
        values = (calories, protein, fat, carbohydrates)
        if any(value < 0 for value in values):
            raise ValueError("Nutrition values cannot be negative")
        return await self.repository.create(
            Product(None, user_id, name, calories, protein, fat, carbohydrates)
        )

    async def search(self, user_id: int, query: str) -> list[Product]:
        return await self.repository.search(user_id, query)

    async def recent(self, user_id: int) -> list[Product]:
        return await self.repository.list_recent(user_id)

    async def get(self, user_id: int, product_id: int) -> Product | None:
        return await self.repository.get(user_id, product_id)
