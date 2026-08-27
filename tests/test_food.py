import unittest
from datetime import datetime, timezone

from app.models.food import FoodEntry
from app.services.food import FoodService


class FoodServiceTests(unittest.TestCase):
    def test_totals(self) -> None:
        entries = [
            FoodEntry(1, 1, "breakfast", "Eggs", 100, 150, 13, 10, 1, datetime.now(timezone.utc)),
            FoodEntry(2, 1, "lunch", "Rice", 200, 260, 5, 1, 56, datetime.now(timezone.utc)),
        ]
        totals = FoodService.totals(entries)
        self.assertEqual(totals, {"calories": 410, "protein": 18, "fat": 11, "carbohydrates": 57})


if __name__ == "__main__":
    unittest.main()
