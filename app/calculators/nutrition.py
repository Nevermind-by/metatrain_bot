from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NutritionResult:
    calories: int
    protein: int
    fat: int
    carbohydrates: int


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "very_high": 1.9,
}


def calculate_nutrition(
    *,
    gender: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
) -> NutritionResult:
    """Calculate daily calories and macros using Mifflin-St Jeor."""
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    elif gender == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        raise ValueError(f"Unsupported gender: {gender}")

    try:
        calories = bmr * ACTIVITY_FACTORS[activity_level]
    except KeyError as error:
        raise ValueError(f"Unsupported activity level: {activity_level}") from error

    if goal == "lose":
        calories *= 0.8
    elif goal == "gain":
        calories *= 1.1
    elif goal != "maintain":
        raise ValueError(f"Unsupported goal: {goal}")

    calories = max(1200, round(calories))
    protein = round(weight_kg * (2.0 if goal == "gain" else 1.8))
    fat = round(weight_kg * 0.9)
    carbohydrates = max(0, round((calories - protein * 4 - fat * 9) / 4))

    return NutritionResult(
        calories=calories,
        protein=protein,
        fat=fat,
        carbohydrates=carbohydrates,
    )
