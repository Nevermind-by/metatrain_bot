from datetime import datetime

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class MacroProgress(BaseModel):
    current: float
    target: float | None = None


class DashboardResponse(BaseModel):
    calories: MacroProgress
    protein: MacroProgress
    fat: MacroProgress
    carbohydrates: MacroProgress
    weight_kg: float | None = None
    workouts_last_7_days: int


class FoodItemResponse(BaseModel):
    id: int
    meal: str
    product_name: str
    grams: float
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    eaten_at: datetime


class FoodTotalsResponse(BaseModel):
    calories: float
    protein: float
    fat: float
    carbohydrates: float


class FoodTodayResponse(BaseModel):
    items: list[FoodItemResponse]
    totals: FoodTotalsResponse


class WeightItemResponse(BaseModel):
    id: int
    weight_kg: float
    measured_at: datetime


class WeightsResponse(BaseModel):
    items: list[WeightItemResponse]


class WeightCreate(BaseModel):
    weight_kg: float = Field(gt=0, le=300)


class FoodCreate(BaseModel):
    meal: str = Field(min_length=1, max_length=32)
    product_name: str = Field(min_length=1, max_length=200)
    grams: float = Field(gt=0)
    calories_per_100: float = Field(ge=0)
    protein_per_100: float = Field(ge=0)
    fat_per_100: float = Field(ge=0)
    carbohydrates_per_100: float = Field(ge=0)
