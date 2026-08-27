import unittest
from unittest.mock import AsyncMock

from app.models.food import FoodEntry
from app.services.food import FoodService


class FoodServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = AsyncMock()
        self.repository.create.side_effect = lambda entry: entry
        self.service = FoodService(self.repository)

    async def test_add_product_rejects_invalid_meal(self):
        with self.assertRaises(ValueError):
            await self.service.add_product_entry(
                user_id=1, meal="invalid", product_name="Rice", grams=100,
                calories_per_100=300, protein_per_100=6, fat_per_100=1,
                carbohydrates_per_100=70,
            )

    async def test_add_product_calculates_macros_from_grams(self):
        entry = await self.service.add_product_entry(
            user_id=1, meal="lunch", product_name=" Rice ", grams=150,
            calories_per_100=300, protein_per_100=6, fat_per_100=2,
            carbohydrates_per_100=70,
        )
        self.assertIsInstance(entry, FoodEntry)
        self.assertEqual(entry.product_name, "Rice")
        self.assertEqual(entry.calories, 450)
        self.assertEqual(entry.protein, 9)
        self.assertEqual(entry.fat, 3)
        self.assertEqual(entry.carbohydrates, 105)

    async def test_recipe_rejects_non_positive_servings(self):
        with self.assertRaises(ValueError):
            await self.service.add_recipe_entry(
                user_id=1, meal="dinner", recipe_name="Soup", servings=0,
                calories_per_serving=200, protein_per_serving=10,
                fat_per_serving=5, carbohydrates_per_serving=20,
            )

    def test_totals(self):
        entries = [
            FoodEntry(1, 1, "lunch", "A", 100, "g", 100, 10, 2, 15, __import__("datetime").datetime.now()),
            FoodEntry(2, 1, "dinner", "B", 100, "g", 200, 20, 5, 25, __import__("datetime").datetime.now()),
        ]
        self.assertEqual(self.service.totals(entries), {"calories": 300, "protein": 30, "fat": 7, "carbohydrates": 40})
