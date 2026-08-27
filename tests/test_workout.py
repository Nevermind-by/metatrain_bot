import unittest

from app.models.workout import WorkoutEntry
from app.services.workout import WorkoutService


class FakeWorkoutRepository:
    def __init__(self) -> None:
        self.created = None
        self.exercise = None
        self.workout = None
        self.workout_set = None

    async def create(self, workout):
        self.created = workout
        workout.id = 1
        return workout

    async def add_exercise(self, exercise):
        self.exercise = exercise
        exercise.id = 2
        return exercise

    async def add_set(self, workout_set):
        self.workout_set = workout_set
        workout_set.id = 3
        return workout_set


class WorkoutServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_strips_name_and_notes(self) -> None:
        repository = FakeWorkoutRepository()
        service = WorkoutService(repository)
        result = await service.start(user_id=10, name="  Push day  ", notes="  chest  ")
        self.assertEqual(result.name, "Push day")
        self.assertEqual(result.notes, "chest")
        self.assertEqual(result.id, 1)

    async def test_start_rejects_blank_name(self) -> None:
        service = WorkoutService(FakeWorkoutRepository())
        with self.assertRaises(ValueError):
            await service.start(user_id=10, name="   ")

    async def test_add_set_validates_rpe(self) -> None:
        service = WorkoutService(FakeWorkoutRepository())
        with self.assertRaises(ValueError):
            await service.add_set(exercise_id=2, set_number=1, weight_kg=50, reps=8, rpe=11)

    async def test_add_set_accepts_valid_values(self) -> None:
        repository = FakeWorkoutRepository()
        service = WorkoutService(repository)
        result = await service.add_set(exercise_id=2, set_number=1, weight_kg=50, reps=8, rpe=8.5)
        self.assertEqual(result.id, 3)
        self.assertEqual(result.weight_kg, 50)
        self.assertEqual(result.reps, 8)
        self.assertEqual(result.rpe, 8.5)


if __name__ == "__main__":
    unittest.main()
