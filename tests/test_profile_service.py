import unittest
from unittest.mock import AsyncMock

from app.models.profile import UserProfile
from app.services.profile import ProfileService


class ProfileServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.repository.upsert.side_effect = lambda profile: profile
        self.service = ProfileService(self.repository)

    async def test_create_profile_calculates_and_persists_nutrition(self):
        profile = await self.service.create_profile(
            user_id=1,
            gender="male",
            age=30,
            height_cm=180,
            weight_kg=80,
            activity_level="moderate",
            goal="maintain",
        )
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.user_id, 1)
        self.assertGreater(profile.calories, 0)
        self.assertGreater(profile.protein, 0)
        self.repository.upsert.assert_awaited_once()

    async def test_invalid_activity_is_rejected(self):
        with self.assertRaises(ValueError):
            await self.service.create_profile(
                user_id=1,
                gender="male",
                age=30,
                height_cm=180,
                weight_kg=80,
                activity_level="unknown",
                goal="maintain",
            )

    async def test_invalid_goal_is_rejected(self):
        with self.assertRaises(ValueError):
            await self.service.create_profile(
                user_id=1,
                gender="male",
                age=30,
                height_cm=180,
                weight_kg=80,
                activity_level="moderate",
                goal="unknown",
            )

    async def test_get_profile_delegates_to_repository(self):
        expected = object()
        self.repository.get_by_user_id.return_value = expected
        result = await self.service.get_profile(42)
        self.assertIs(result, expected)
        self.repository.get_by_user_id.assert_awaited_once_with(42)
