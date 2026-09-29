import unittest

from app.services.smart_food import detect_meal, parse_food_text


class SmartFoodParserTests(unittest.TestCase):
    def test_parse_free_form_list(self):
        items = parse_food_text(
            "Рис отварной 150г\n"
            "Рубленные куриные котлеты 100г\n"
            "Масло сливочное 82% 5г"
        )
        self.assertEqual(
            [(item.raw_name, item.amount) for item in items],
            [
                ("Рис отварной", 150.0),
                ("Рубленные куриные котлеты", 100.0),
                ("Масло сливочное 82%", 5.0),
            ],
        )

    def test_parse_reordered_quantities(self):
        items = parse_food_text("масло 5 г, рис 150г, куриные котлеты 100 гр")
        self.assertEqual([item.amount for item in items], [5.0, 150.0, 100.0])

    def test_parse_meal_label(self):
        self.assertEqual(detect_meal("Завтрак\nрис 150г"), "breakfast")

    def test_parse_free_prose(self):
        items = parse_food_text("съел 150г риса, 100 г котлет и 5г масла")
        self.assertEqual(len(items), 3)
        self.assertEqual([item.amount for item in items], [150.0, 100.0, 5.0])


if __name__ == "__main__":
    unittest.main()
