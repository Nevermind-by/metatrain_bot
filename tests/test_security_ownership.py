import unittest
from unittest.mock import AsyncMock

from app.repositories.workout import WorkoutRepository


class OwnershipRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_workout_lookup_always_uses_user_id(self):
        db = AsyncMock()
        repo = WorkoutRepository(db)
        await repo.get_workout(123, 456)
        db.execute.assert_awaited_once()
        query = db.execute.await_args.args[0]
        self.assertIn("workouts.user_id", str(query))

    async def test_workout_exercise_lookup_uses_user_id(self):
        db = AsyncMock()
        repo = WorkoutRepository(db)
        await repo.get_exercise(123, 456)
        db.execute.assert_awaited_once()
        query = db.execute.await_args.args[0]
        self.assertIn("workouts.user_id", str(query))

    async def test_set_lookup_uses_user_id(self):
        db = AsyncMock()
        repo = WorkoutRepository(db)
        await repo.get_set(123, 456)
        db.execute.assert_awaited_once()
        query = db.execute.await_args.args[0]
        self.assertIn("workouts.user_id", str(query))
