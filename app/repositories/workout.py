from datetime import datetime, timezone

from app.database.connection import get_connection
from app.models.workout import WorkoutEntry


class WorkoutRepository:
    async def create(self, entry: WorkoutEntry) -> WorkoutEntry:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                """
                INSERT INTO workout_entries (
                    user_id, name, duration_minutes, calories_burned, notes, performed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.user_id,
                    entry.name,
                    entry.duration_minutes,
                    entry.calories_burned,
                    entry.notes,
                    entry.performed_at.isoformat(),
                ),
            )
            await connection.commit()
            entry.id = cursor.lastrowid
        return entry

    async def recent(self, user_id: int, limit: int = 20) -> list[WorkoutEntry]:
        async with await get_connection() as connection:
            cursor = await connection.execute(
                "SELECT * FROM workout_entries WHERE user_id = ? ORDER BY performed_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> WorkoutEntry:
        performed_at = datetime.fromisoformat(row["performed_at"])
        if performed_at.tzinfo is None:
            performed_at = performed_at.replace(tzinfo=timezone.utc)
        return WorkoutEntry(
            row["id"], row["user_id"], row["name"], row["duration_minutes"],
            row["calories_burned"], row["notes"], performed_at,
        )
