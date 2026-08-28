from datetime import UTC, datetime

from app.models.workout import WorkoutEntry, WorkoutExercise, WorkoutSet
from app.repositories.workout import WorkoutRepository


class WorkoutService:
    def __init__(self, repository: WorkoutRepository | None = None) -> None:
        self.repository = repository or WorkoutRepository()

    async def start(self, *, user_id: int, name: str, notes: str | None = None) -> WorkoutEntry:
        if not name.strip():
            raise ValueError("Workout name is required")
        return await self.repository.create(
            WorkoutEntry(None, user_id, name.strip(), None, None, notes.strip() if notes else None, datetime.now(UTC))
        )

    async def add_exercise(self, *, workout_id: int, name: str, position: int) -> WorkoutExercise:
        if not name.strip() or position < 1:
            raise ValueError("Invalid exercise")
        return await self.repository.add_exercise(WorkoutExercise(None, workout_id, name.strip(), position))

    async def add_set(self, *, exercise_id: int, set_number: int, weight_kg: float, reps: int, rpe: float | None = None) -> WorkoutSet:
        if set_number < 1 or weight_kg < 0 or reps < 1 or (rpe is not None and not 1 <= rpe <= 10):
            raise ValueError("Invalid set")
        return await self.repository.add_set(WorkoutSet(None, exercise_id, set_number, weight_kg, reps, rpe))

    async def delete_set(self, *, set_id: int, user_id: int) -> bool:
        return await self.repository.delete_set_for_user(set_id, user_id)

    async def complete(self, *, user_id: int, workout_id: int, duration_minutes: int | None = None, calories_burned: float | None = None) -> WorkoutEntry | None:
        if duration_minutes is not None and duration_minutes < 0:
            raise ValueError("Invalid duration")
        if calories_burned is not None and calories_burned < 0:
            raise ValueError("Invalid calories")
        return await self.repository.complete(workout_id, user_id, duration_minutes, calories_burned)

    async def recent(self, user_id: int, limit: int = 10) -> list[WorkoutEntry]:
        return await self.repository.recent(user_id, limit)

    async def get_workout_for_user(self, workout_id: int, user_id: int) -> WorkoutEntry | None:
        return await self.repository.get_workout_for_user(workout_id, user_id)

    async def get_exercise_for_user(self, exercise_id: int, user_id: int) -> WorkoutExercise | None:
        return await self.repository.get_exercise_for_user(exercise_id, user_id)

    async def exercise_history(self, user_id: int, exercise_name: str, limit: int = 100) -> list[WorkoutSet]:
        return await self.repository.exercise_history(user_id, exercise_name, limit)

    async def latest_set_for_exercise(self, user_id: int, exercise_name: str) -> WorkoutSet | None:
        return await self.repository.latest_set_for_exercise(user_id, exercise_name)

    async def progress(self, user_id: int, exercise_name: str, limit: int = 20) -> dict:
        sessions = await self.repository.exercise_workout_history(user_id, exercise_name, limit)
        sets = await self.repository.exercise_history(user_id, exercise_name, 100)
        if not sets:
            return {"exercise": exercise_name, "sets": [], "sessions": [], "best_weight": 0, "best_volume": 0, "estimated_1rm": 0}
        best_weight = max(item.weight_kg for item in sets)
        best_volume = max(item.weight_kg * item.reps for item in sets)
        estimated_1rm = max((item.weight_kg * (1 + item.reps / 30) for item in sets if item.weight_kg > 0), default=0)
        return {
            "exercise": exercise_name,
            "sets": sets,
            "sessions": sessions,
            "best_weight": round(best_weight, 1),
            "best_volume": round(best_volume, 1),
            "estimated_1rm": round(estimated_1rm, 1),
        }
