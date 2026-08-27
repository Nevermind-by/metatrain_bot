from datetime import datetime, timedelta, timezone

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

    async def analytics(self, user_id: int, limit: int = 90) -> dict:
        entries = await self.repository.recent(user_id, limit)
        if not entries:
            return {"current": None, "change_7d": None, "change_30d": None, "min": None, "max": None, "trend": None, "entries": []}

        now = datetime.now(timezone.utc)
        current = entries[0].weight_kg

        def weight_before(days: int) -> float | None:
            cutoff = now - timedelta(days=days)
            candidates = [item for item in entries if item.measured_at <= cutoff]
            return candidates[-1].weight_kg if candidates else None

        week = weight_before(7)
        month = weight_before(30)
        values = [item.weight_kg for item in entries]
        oldest = values[-1]
        trend = "up" if current > oldest else "down" if current < oldest else "stable"
        return {
            "current": current,
            "change_7d": round(current - week, 2) if week is not None else None,
            "change_30d": round(current - month, 2) if month is not None else None,
            "min": min(values),
            "max": max(values),
            "trend": trend,
            "entries": [{"id": item.id, "weight_kg": item.weight_kg, "measured_at": item.measured_at.isoformat()} for item in entries],
        }
