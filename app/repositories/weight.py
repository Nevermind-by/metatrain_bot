from datetime import datetime, timezone

from app.database.connection import get_connection
from app.models.weight import WeightEntry


class WeightRepository:
    async def create(self, entry: WeightEntry) -> WeightEntry:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "INSERT INTO weight_entries (user_id, weight_kg, measured_at) VALUES (?, ?, ?)",
                (entry.user_id, entry.weight_kg, entry.measured_at.isoformat()),
            )
            await connection.commit()
            entry.id = cursor.lastrowid
        return entry

    async def latest(self, user_id: int) -> WeightEntry | None:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM weight_entries WHERE user_id = ? ORDER BY measured_at DESC LIMIT 1",
                (user_id,),
            )
            row = await cursor.fetchone()
        return self._to_model(row) if row else None

    async def recent(self, user_id: int, limit: int = 10) -> list[WeightEntry]:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM weight_entries WHERE user_id = ? ORDER BY measured_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> WeightEntry:
        measured_at = datetime.fromisoformat(row["measured_at"])
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        return WeightEntry(row["id"], row["user_id"], row["weight_kg"], measured_at)
