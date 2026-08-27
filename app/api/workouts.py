from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.router import current_telegram_id, get_user
from app.services.workout import WorkoutService

router = APIRouter(prefix="/api/workouts", tags=["workouts"])
service = WorkoutService()


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class WorkoutComplete(BaseModel):
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    calories_burned: float | None = Field(default=None, ge=0, le=10000)


class ExerciseCreate(BaseModel):
    workout_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    position: int = Field(ge=1)


class SetCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    set_number: int = Field(ge=1)
    weight_kg: float = Field(ge=0, le=1000)
    reps: int = Field(ge=1, le=1000)
    rpe: float | None = Field(default=None, ge=1, le=10)


@router.get("")
async def workouts(telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    return {"items": [item.__dict__ for item in await service.recent(user.id)]}


@router.post("")
async def create_workout(payload: WorkoutCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    return (await service.start(user_id=user.id, name=payload.name, notes=payload.notes)).__dict__


@router.post("/exercises")
async def add_exercise(payload: ExerciseCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    if await service.get_workout_for_user(payload.workout_id, user.id) is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return (await service.add_exercise(workout_id=payload.workout_id, name=payload.name, position=payload.position)).__dict__


@router.post("/sets")
async def add_set(payload: SetCreate, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    exercise = await service.get_exercise_for_user(payload.exercise_id, user.id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return (await service.add_set(exercise_id=payload.exercise_id, set_number=payload.set_number, weight_kg=payload.weight_kg, reps=payload.reps, rpe=payload.rpe)).__dict__


@router.post("/{workout_id}/complete")
async def complete_workout(workout_id: int, payload: WorkoutComplete, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    workout = await service.complete(user_id=user.id, workout_id=workout_id, duration_minutes=payload.duration_minutes, calories_burned=payload.calories_burned)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout.__dict__


@router.delete("/sets/{set_id}")
async def delete_set(set_id: int, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    if not await service.delete_set(set_id=set_id, user_id=user.id):
        raise HTTPException(status_code=404, detail="Set not found")
    return {"deleted": True}


@router.get("/progress/{exercise_name}")
async def progress(exercise_name: str, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    result = await service.progress(user.id, exercise_name)
    return {"exercise": result["exercise"], "best_weight": result["best_weight"], "best_volume": result["best_volume"], "estimated_1rm": result["estimated_1rm"], "sets": [item.__dict__ for item in result["sets"]]}


@router.get("/{workout_id}")
async def workout(workout_id: int, telegram_id: int = Depends(current_telegram_id)):
    user = await get_user(telegram_id)
    item = await service.get_workout_for_user(workout_id, user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    exercises = await service.repository.exercises_with_sets_for_workout(workout_id)
    return {"workout": item.__dict__, "exercises": [{"exercise": exercise.__dict__, "sets": [workout_set.__dict__ for workout_set in sets]} for exercise, sets in exercises]}
