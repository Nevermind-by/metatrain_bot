import unittest

from app.services.workout import WorkoutService


class FakeWorkoutRepository:
    def __init__(self) -> None:
        self.created = None
        self.exercise = None
        self.workout = None
        self.workout_set = None
        self.active_workout = None
        self.updated = None

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

    async def get_set_for_user(self, set_id, user_id):
        if set_id != 3:
            return None
        return self.workout_set

    async def update_set_for_user(self, workout_set, user_id):
        self.updated = workout_set
        return True

    async def cancel_active(self, workout_id, user_id):
        return workout_id == 10 and user_id == 20

    async def active_for_user(self, user_id):
        return self.active_workout


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

    async def test_update_set_changes_values(self) -> None:
        repository = FakeWorkoutRepository()
        original = await repository.add_set(WorkoutService(repository).repository and __import__("app.models.workout", fromlist=["WorkoutSet"]).WorkoutSet(None, 2, 1, 50, 8, 8))
        service = WorkoutService(repository)
        result = await service.update_set(set_id=3, user_id=20, weight_kg=55, reps=10, rpe=9)
        self.assertIsNotNone(result)
        self.assertEqual(repository.updated.weight_kg, 55)
        self.assertEqual(repository.updated.reps, 10)
        self.assertEqual(repository.updated.rpe, 9)

    async def test_update_set_rejects_invalid_reps(self) -> None:
        service = WorkoutService(FakeWorkoutRepository())
        with self.assertRaises(ValueError):
            await service.update_set(set_id=3, user_id=20, weight_kg=50, reps=0, rpe=8)

    async def test_cancel_active_delegates_to_repository(self) -> None:
        service = WorkoutService(FakeWorkoutRepository())
        self.assertTrue(await service.cancel_active(user_id=20, workout_id=10))
        self.assertFalse(await service.cancel_active(user_id=20, workout_id=11))

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
