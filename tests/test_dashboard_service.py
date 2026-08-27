import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from app.models.food import FoodEntry
from app.models.profile import UserProfile
from app.models.weight import WeightEntry
from app.models.workout import WorkoutEntry
from app.services.dashboard import DashboardService


class DashboardServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = DashboardService()
        self.service.profile = AsyncMock()
        self.service.food = AsyncMock()
        self.service.weight = AsyncMock()
        self.service.workout = AsyncMock()
        self.service.food.totals = lambda entries: {
            "calories": sum(x.calories for x in entries),
            "protein": sum(x.protein for x in entries),
            "fat": sum(x.fat for x in entries),
            "carbohydrates": sum(x.carbohydrates for x in entries),
        }

    async def test_build_aggregates_today_and_week(self):
        now = datetime.now(UTC)
        self.service.profile.get_profile.return_value = UserProfile(1, "male", 30, 180, 80, "moderate", "maintain", 2500, 160, 80, 300)
        self.service.food.today.return_value = [
            FoodEntry(1, 1, "lunch", "Rice", 100, "g", 350, 7, 1, 75, now),
        ]
        self.service.weight.latest.return_value = WeightEntry(1, 1, 80, now)
        self.service.workout.recent.return_value = [
            WorkoutEntry(1, 1, "Today", None, None, None, now),
            WorkoutEntry(2, 1, "Old", None, None, None, now - timedelta(days=8)),
        ]

        result = await self.service.build(1)

        self.assertIn("🔥 Калории: 350 / 2500", result)
        self.assertIn("🥩 Белки: 7 г / 160 г", result)
        self.assertIn("⚖️ Вес: 80 кг", result)
        self.assertIn("🏋️ Тренировок за 7 дней: 1", result)

    async def test_build_handles_missing_profile_and_weight(self):
        self.service.profile.get_profile.return_value = None
        self.service.food.today.return_value = []
        self.service.weight.latest.return_value = None
        self.service.workout.recent.return_value = []

        result = await self.service.build(1)

        self.assertIn("🔥 Калории: 0", result)
        self.assertIn("⚖️ Вес: нет измерений", result)
        self.assertIn("🏋️ Тренировок за 7 дней: 0", result)
