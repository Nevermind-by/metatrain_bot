from datetime import datetime, timezone

from app.models.workout import WorkoutEntry
from app.repositories.workout import WorkoutRepository


class WorkoutService:
    def __init__(self, repository: WorkoutRepository | None = None) -> None:
        self.repository = repository or WorkoutRepository()

    async def add(
        self,
        *,
        user_id: int,
        name: str,
        duration_minutes: int | None = None,
        calories_burned: int | None = None,
        notes: str | None = None,
    ) -> WorkoutEntry:
        if not name.strip():
            raise ValueError("Workout name is required")
        if duration_minutes is not None and not 1 <= duration_minutes <= 1440:
            raise ValueError("Invalid duration")
        if calories_burned is not None and calories_burned < 0:
            raise ValueError("Calories burned cannot be negative")
        return await self.repository.create(
            WorkoutEntry(
                None, user_id, name.strip(), duration_minutes,
                calories_burned, notes.strip() if notes else None,
                datetime.now(timezone.utc),
            )
        )

    async def recent(self, user_id: int, limit: int = 10) -> list[WorkoutEntry]:
        return await self.repository.recent(user_id, limit)
