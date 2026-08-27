import unittest
from unittest.mock import AsyncMock, patch

from app.repositories.workout import WorkoutRepository


class OwnershipRegressionTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.repositories.workout.get_connection")
    async def test_workout_lookup_always_uses_user_id(self, get_connection):
        connection = AsyncMock()
        cursor = AsyncMock()
        cursor.fetchone.return_value = None
        connection.execute.return_value = cursor
        get_connection.return_value = connection

        repo = WorkoutRepository()
        await repo.get_workout_for_user(123, 456)
        query, params = connection.execute.await_args.args
        self.assertIn("user_id=?", str(query))
        self.assertEqual(params, (123, 456))

    @patch("app.repositories.workout.get_connection")
    async def test_workout_exercise_lookup_uses_user_id(self, get_connection):
        connection = AsyncMock()
        cursor = AsyncMock()
        cursor.fetchone.return_value = None
        connection.execute.return_value = cursor
        get_connection.return_value = connection

        repo = WorkoutRepository()
        await repo.get_exercise_for_user(123, 456)
        query, params = connection.execute.await_args.args
        self.assertIn("w.user_id=?", str(query))
        self.assertEqual(params, (123, 456))

    @patch("app.repositories.workout.get_connection")
    async def test_set_lookup_uses_user_id(self, get_connection):
        connection = AsyncMock()
        cursor = AsyncMock()
        cursor.fetchone.return_value = None
        connection.execute.return_value = cursor
        get_connection.return_value = connection

        repo = WorkoutRepository()
        await repo.get_set_for_user(123, 456)
        query, params = connection.execute.await_args.args
        self.assertIn("w.user_id=?", str(query))
        self.assertEqual(params, (123, 456))
