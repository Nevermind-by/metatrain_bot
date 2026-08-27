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
            workout_set.id = cursor.lastrowid
            await connection.commit()
        return workout_set

    async def recent(self, user_id: int, limit: int = 10) -> list[WorkoutEntry]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT * FROM workout_entries WHERE user_id=? ORDER BY performed_at DESC LIMIT ?", (user_id, limit))
            rows = await cursor.fetchall()
        return [self._workout(row) for row in rows]

    async def exercise_history(self, user_id: int, exercise_name: str, limit: int = 10) -> list[WorkoutSet]:
        async with await get_connection() as connection:
            cursor = await connection.execute("SELECT s.* FROM workout_sets s JOIN workout_exercises e ON e.id=s.exercise_id JOIN workout_entries w ON w.id=e.workout_id WHERE w.user_id=? AND lower(e.name)=lower(?) ORDER BY w.performed_at DESC, s.set_number LIMIT ?", (user_id, exercise_name.strip(), limit))
            rows = await cursor.fetchall()
        return [WorkoutSet(row["id"], row["exercise_id"], row["set_number"], row["weight_kg"], row["reps"], row["rpe"]) for row in rows]

    @staticmethod
    def _workout(row) -> WorkoutEntry:
        performed_at = datetime.fromisoformat(row["performed_at"])
        if performed_at.tzinfo is None: performed_at = performed_at.replace(tzinfo=timezone.utc)
        return WorkoutEntry(row["id"], row["user_id"], row["name"], row["duration_minutes"], row["calories_burned"], row["notes"], performed_at)
