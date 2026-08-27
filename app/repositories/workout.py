from datetime import datetime, timezone

from app.database.connection import get_connection
from app.models.workout import WorkoutEntry, WorkoutExercise, WorkoutSet


class WorkoutRepository:
    async def create(self, workout: WorkoutEntry) -> WorkoutEntry:
        async with await get_connection() as connection:
            cursor = await connection.execute("INSERT INTO workout_entries (user_id,name,duration_minutes,calories_burned,notes,performed_at) VALUES (?,?,?,?,?,?)", (workout.user_id, workout.name, workout.duration_minutes, workout.calories_burned, workout.notes, workout.performed_at.isoformat()))
            workout.id = cursor.lastrowid
            await connection.commit()
        return workout

    async def add_exercise(self, exercise: WorkoutExercise) -> WorkoutExercise:
        async with await get_connection() as connection:
            cursor = await connection.execute("INSERT INTO workout_exercises (workout_id,name,position) VALUES (?,?,?)", (exercise.workout_id, exercise.name, exercise.position))
            exercise.id = cursor.lastrowid
            await connection.commit()
        return exercise

    async def add_set(self, workout_set: WorkoutSet) -> WorkoutSet:
        async with await get_connection() as connection:
            cursor = await connection.execute("INSERT INTO workout_sets (exercise_id,set_number,weight_kg,reps,rpe) VALUES (?,?,?,?,?)", (workout_set.exercise_id, workout_set.set_number, workout_set.weight_kg, workout_set.reps, workout_set.rpe))
            await connection.commit()
        return workout_set

    async def sets_for_exercise(self, exercise_id: int) -> list[WorkoutSet]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM workout_sets WHERE exercise_id=? ORDER BY set_number", (exercise_id,))
            rows = await cursor.fetchall()
        return [WorkoutSet(row["id"], row["exercise_id"], row["set_number"], row["weight_kg"], row["reps"], row["rpe"]) for row in rows]

    async def exercises_with_sets_for_workout(self, workout_id: int) -> list[tuple[WorkoutExercise, list[WorkoutSet]]]:
        exercises = await self.exercises_for_workout(workout_id)
        result = []
        for exercise in exercises:
            result.append((exercise, await self.sets_for_exercise(exercise.id)))
        return result

    async def delete_set_for_user(self, set_id: int, user_id: int) -> bool:
        async with await get_connection() as connection:
            cursor = await connection.execute("DELETE FROM workout_sets WHERE id=? AND exercise_id IN (SELECT e.id FROM workout_exercises e JOIN workout_entries w ON w.id=e.workout_id WHERE w.user_id=?)", (set_id, user_id))
            await connection.commit()
        return cursor.rowcount > 0

    async def complete(self, workout_id: int, user_id: int, duration_minutes: int | None, calories_burned: float | None) -> WorkoutEntry | None:
        async with await get_connection() as connection:
            cursor = await connection.execute("UPDATE workout_entries SET duration_minutes=?, calories_burned=? WHERE id=? AND user_id=?", (duration_minutes, calories_burned, workout_id, user_id))
            await connection.commit()
            if cursor.rowcount == 0: return None
            cursor = await connection.execute("SELECT * FROM workout_entries WHERE id=? AND user_id=?", (workout_id, user_id))
            row = await cursor.fetchone()
        return self._workout(row) if row else None

    async def recent(self, user_id: int, limit: int = 10) -> list[WorkoutEntry]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM workout_entries WHERE user_id=? ORDER BY performed_at DESC LIMIT ?", (user_id, limit))
            rows = await cursor.fetchall()
        return [self._workout(row) for row in rows]

    async def get_workout_for_user(self, workout_id: int, user_id: int) -> WorkoutEntry | None:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM workout_entries WHERE id=? AND user_id=?", (workout_id, user_id))
            row = await cursor.fetchone()
        return self._workout(row) if row else None

    async def get_exercise_for_user(self, exercise_id: int, user_id: int) -> WorkoutExercise | None:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT e.* FROM workout_exercises e JOIN workout_entries w ON w.id=e.workout_id WHERE e.id=? AND w.user_id=?", (exercise_id, user_id))
            row = await cursor.fetchone()
        return WorkoutExercise(row["id"], row["workout_id"], row["name"], row["position"]) if row else None

    async def exercises_for_workout(self, workout_id: int) -> list[WorkoutExercise]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM workout_exercises WHERE workout_id=? ORDER BY position", (workout_id,))
            rows = await cursor.fetchall()
        return [WorkoutExercise(row["id"], row["workout_id"], row["name"], row["position"]) for row in rows]

    async def exercise_history(self, user_id: int, exercise_name: str, limit: int = 100) -> list[WorkoutSet]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT s.* FROM workout_sets s JOIN workout_exercises e ON e.id=s.exercise_id JOIN workout_entries w ON w.id=e.workout_id WHERE w.user_id=? AND lower(e.name)=lower(?) ORDER BY w.performed_at DESC, s.set_number LIMIT ?", (user_id, exercise_name.strip(), limit))
            rows = await cursor.fetchall()
        return [WorkoutSet(row["id"], row["exercise_id"], row["set_number"], row["weight_kg"], row["reps"], row["rpe"]) for row in rows]

    async def exercise_workout_history(self, user_id: int, exercise_name: str, limit: int = 30) -> list[dict]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT w.id AS workout_id, w.performed_at, MAX(s.weight_kg) AS max_weight, SUM(s.weight_kg * s.reps) AS volume, MAX(s.weight_kg * (1 + s.reps / 30.0)) AS estimated_1rm, COUNT(s.id) AS sets_count FROM workout_entries w JOIN workout_exercises e ON e.workout_id=w.id JOIN workout_sets s ON s.exercise_id=e.id WHERE w.user_id=? AND lower(e.name)=lower(?) GROUP BY w.id, w.performed_at ORDER BY w.performed_at DESC LIMIT ?", (user_id, exercise_name.strip(), limit))
            rows = await cursor.fetchall()
        return [{"workout_id": row["workout_id"], "performed_at": row["performed_at"], "max_weight": round(row["max_weight"] or 0, 1), "volume": round(row["volume"] or 0, 1), "estimated_1rm": round(row["estimated_1rm"] or 0, 1), "sets_count": row["sets_count"]} for row in rows]

    @staticmethod
    def _workout(row) -> WorkoutEntry:
        performed_at = datetime.fromisoformat(row["performed_at"])
        if performed_at.tzinfo is None: performed_at = performed_at.replace(tzinfo=timezone.utc)
        return WorkoutEntry(row["id"], row["user_id"], row["name"], row["duration_minutes"], row["calories_burned"], row["notes"], performed_at)
