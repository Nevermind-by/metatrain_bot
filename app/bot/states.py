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
