import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.auth import validate_telegram_init_data
from app.api.schemas import DashboardResponse, FoodCreate, FoodItemResponse, FoodTodayResponse, FoodTotalsResponse, MacroProgress, UserResponse, WeightCreate, WeightItemResponse, WeightsResponse
from app.services.dashboard import DashboardService
from app.services.food import FoodService
from app.services.user import UserService
from app.services.weight import WeightService

router = APIRouter(prefix="/api")
user_service = UserService()
dashboard_service = DashboardService()
food_service = FoodService()
weight_service = WeightService()


def current_telegram_id(x_telegram_init_data: str = Header(...)) -> int:
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")
    try:
        data = validate_telegram_init_data(x_telegram_init_data, bot_token)
        user = json.loads(data["user"])
        return int(user["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid Telegram Web App authentication")


async def get_user(telegram_id: int):
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserResponse)
async def me(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    profile = await dashboard_service.profile.get_profile(user.id)
    foods = await dashboard_service.food.today(user.id)
    totals = dashboard_service.food.totals(foods)
    latest_weight = await dashboard_service.weight.latest(user.id)
    workouts = await dashboard_service.workout.recent(user.id, 50)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    return DashboardResponse(
        calories=MacroProgress(current=totals["calories"], target=profile.calories if profile else None),
        protein=MacroProgress(current=totals["protein"], target=profile.protein if profile else None),
        fat=MacroProgress(current=totals["fat"], target=profile.fat if profile else None),
        carbohydrates=MacroProgress(current=totals["carbohydrates"], target=profile.carbohydrates if profile else None),
        weight_kg=latest_weight.weight_kg if latest_weight else None,
        workouts_last_7_days=sum(item.performed_at >= since for item in workouts),
    )


@router.get("/food/today", response_model=FoodTodayResponse)
async def food_today(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    entries = await food_service.today(user.id)
    return FoodTodayResponse(items=[FoodItemResponse.model_validate(entry, from_attributes=True) for entry in entries], totals=FoodTotalsResponse(**food_service.totals(entries)))


@router.post("/food", response_model=FoodItemResponse)
async def add_food(payload: FoodCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    entry = await food_service.add_product_entry(user_id=user.id, **payload.model_dump())
    return FoodItemResponse.model_validate(entry, from_attributes=True)


@router.get("/weights", response_model=WeightsResponse)
async def weights(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    entries = await weight_service.recent(user.id)
    return WeightsResponse(items=[WeightItemResponse.model_validate(entry, from_attributes=True) for entry in entries])


@router.post("/weights", response_model=WeightItemResponse)
async def add_weight(payload: WeightCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    entry = await weight_service.add(user.id, payload.weight_kg)
    return WeightItemResponse.model_validate(entry, from_attributes=True)
