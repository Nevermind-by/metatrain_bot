import unittest

from app.calculators.nutrition import calculate_nutrition


class NutritionCalculatorTests(unittest.TestCase):
    def test_male_maintenance_uses_activity_factor(self) -> None:
        result = calculate_nutrition(
            gender="male",
            age=30,
            height_cm=180,
            weight_kg=80,
            activity_level="moderate",
            goal="maintain",
        )
        self.assertGreater(result.calories, 2000)
        self.assertGreater(result.protein, 0)
        self.assertGreater(result.fat, 0)
        self.assertGreater(result.carbohydrates, 0)

    def test_female_cut_is_lower_than_maintenance(self) -> None:
        maintain = calculate_nutrition(
            gender="female", age=30, height_cm=165, weight_kg=65,
            activity_level="light", goal="maintain",
        )
        lose = calculate_nutrition(
            gender="female", age=30, height_cm=165, weight_kg=65,
            activity_level="light", goal="lose",
        )
        self.assertLess(lose.calories, maintain.calories)


if __name__ == "__main__":
    unittest.main()
