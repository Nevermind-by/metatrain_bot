import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.models.weight import WeightEntry
from app.services.weight import WeightService


class WeightServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.service = WeightService(self.repository)

    async def test_add_rejects_weight_outside_supported_range(self):
        for weight in (29.9, 300.1):
            with self.subTest(weight=weight):
                with self.assertRaises(ValueError):
                    await self.service.add(1, weight)
        self.repository.create.assert_not_awaited()

    async def test_add_creates_entry_for_valid_weight(self):
        expected = WeightEntry(7, 1, 82.5, datetime.now(timezone.utc))
        self.repository.create.return_value = expected
        result = await self.service.add(1, 82.5)
        self.assertIs(result, expected)
        self.repository.create.assert_awaited_once()

    async def test_analytics_returns_empty_state_without_measurements(self):
        self.repository.recent.return_value = []
        result = await self.service.analytics(1)
        self.assertEqual(result["current"], None)
        self.assertEqual(result["entries"], [])
        self.assertIsNone(result["change_7d"])
        self.assertIsNone(result["trend"])

    async def test_analytics_calculates_changes_and_extremes(self):
        now = datetime.now(timezone.utc)
        self.repository.recent.return_value = [
            WeightEntry(3, 1, 78.0, now - timedelta(days=31)),
            WeightEntry(2, 1, 80.0, now - timedelta(days=8)),
            WeightEntry(1, 1, 79.0, now),
        ]
        result = await self.service.analytics(1, limit=90)
        self.assertEqual(result["current"], 79.0)
        self.assertEqual(result["change_7d"], -1.0)
        self.assertEqual(result["change_30d"], 1.0)
        self.assertEqual(result["min"], 78.0)
        self.assertEqual(result["max"], 80.0)
        self.assertEqual(result["trend"], "up")
        self.assertEqual(len(result["entries"]), 3)
