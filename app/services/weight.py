from datetime import datetime, timezone

from app.models.weight import WeightEntry
from app.repositories.weight import WeightRepository


class WeightService:
    def __init__(self, repository: WeightRepository | None = None) -> None:
        self.repository = repository or WeightRepository()

    async def add(self, user_id: int, weight_kg: float) -> WeightEntry:
        if not 30 <= weight_kg <= 300:
            raise ValueError("Weight must be between 30 and 300 kg")
        return await self.repository.create(
            WeightEntry(None, user_id, weight_kg, datetime.now(timezone.utc))
        )

    async def latest(self, user_id: int) -> WeightEntry | None:
        return await self.repository.latest(user_id)

    async def recent(self, user_id: int, limit: int = 10) -> list[WeightEntry]:
        return await self.repository.recent(user_id, limit)
