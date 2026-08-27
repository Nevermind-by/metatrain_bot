from dataclasses import dataclass


@dataclass(slots=True)
class Recipe:
    id: int | None
    user_id: int
    name: str
    servings: int
    calories: float
    protein: float
    fat: float
    carbohydrates: float


@dataclass(slots=True)
class RecipeIngredient:
    id: int | None
    recipe_id: int
    product_id: int
    grams: float
