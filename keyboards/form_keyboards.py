from typing import Dict, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_survey_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    user_id = data['user_id']
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Start survey", callback_data=f'start_survey_{user_id}')]
        ]
    )


def get_answers_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    buttons = list()
    ind = data['current_index']
    questions = data['questions']
    user_id = data['user_id']
    ikb = None
    if ind in range(len(questions)):
        question = questions[ind]
        answers = question[1]
        for element in answers:
            buttons.append(InlineKeyboardButton(text=element, callback_data=f"ans_{hash(element)}_{user_id}", ))
        ikb = InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])
    return ikb
