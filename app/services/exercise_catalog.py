from app.models.exercise import ExerciseCatalogItem
from app.repositories.exercise_catalog import ExerciseCatalogRepository


class ExerciseCatalogService:
    def __init__(self, repository: ExerciseCatalogRepository | None = None) -> None:
        self.repository = repository or ExerciseCatalogRepository()

    async def list_by_category(self, category: str) -> list[ExerciseCatalogItem]:
        return await self.repository.list_by_category(category)

    async def get(self, exercise_id: int) -> ExerciseCatalogItem | None:
        return await self.repository.get(exercise_id)

    async def search(self, query: str, limit: int = 20) -> list[ExerciseCatalogItem]:
        return await self.repository.search(query, limit)
