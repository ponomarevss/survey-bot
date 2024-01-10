from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    user_id = State()
    user_name = State()
    current_index = State()
    questions = State()
    answers = State()
