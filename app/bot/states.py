from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity_level = State()
    goal = State()
    edit_gender = State()
    edit_age = State()
    edit_height = State()
    edit_weight = State()
    edit_activity_level = State()
    edit_goal = State()


class FoodStates(StatesGroup):
    meal = State()
    product_name = State()
    grams = State()
    calories = State()
    protein = State()
    fat = State()
    carbohydrates = State()
    recipe = State()


class ProductStates(StatesGroup):
    name = State()
    calories = State()
    protein = State()
    fat = State()
    carbohydrates = State()


class RecipeStates(StatesGroup):
    name = State()
    servings = State()
    product = State()
    grams = State()


class WeightStates(StatesGroup):
    value = State()


class WorkoutStates(StatesGroup):
    category = State()
    exercise = State()
    weight = State()
    reps = State()
    rpe = State()


class ProgressStates(StatesGroup):
    exercise = State()
