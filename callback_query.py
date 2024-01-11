import random
import uuid
from typing import Dict, Any, List

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from source import questions_source
from states import Form


async def command_start_message_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(user_id=str(uuid.uuid4()))
    text = (f"Hello and welcome!\n"
            f"How can I call you? (Type in your first name and last name)")
    await state.set_state(Form.user_name)
    await message.answer(text=text)


async def init_state_message_handler(message: Message, state: FSMContext) -> None:
    size = 10
    data = await state.update_data(
        user_name=message.text,
        current_index=0,
        questions=random.sample(questions_source, size),
        answers=[None for _ in range(size)]
    )
    await state.set_state(Form.answers)
    text = (f"Dear {data['user_name']}, let's begin our survey.\n"
            f"Please, proceed with 'Start survey' button, if you are ready.")
    await message.answer(text=text, reply_markup=get_start_survey_ikb(data))


async def unknown_message_handler(message: Message):
    await message.reply(
        text='Unknown message. Use buttons to continue current session or command "/start" to start new one.'
    )


async def start_survey_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    if data['user_id'] == callback.data.split('_')[2]:
        # check if button used in current session,
        # otherwise incorrect_button_usage

        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        next_index = data['current_index'] + 1
        await state.update_data(current_index=next_index)
    else:
        await incorrect_button_usage_callback_handler(callback)


async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    if data['user_id'] == callback.data.split('_')[2]:
        # check if button used in current session,
        # otherwise incorrect_button_usage

        await state.update_data(answers=update_answers(callback.data, data))

        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        current_index = data['current_index']
        if current_index in range(0, len(data['questions'])):
            next_index = data['current_index'] + 1
            await state.update_data(current_index=next_index)
        else:
            await state.set_state(None)

    else:
        await incorrect_button_usage_callback_handler(callback)


async def incorrect_button_usage_callback_handler(callback: CallbackQuery):
    text = callback.message.text
    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer("Incorrect button usage.")


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


def compose_text(data: Dict[str, Any]) -> str:
    questions = data['questions']
    current_index = data['current_index']
    answers = data['answers']
    name = data['user_name']
    text = f'Candidate {name}\n\n'
    for i in range(current_index + 1):
        prev_index = i - 1  # index for answer to previous question
        if prev_index in range(len(questions)):
            text += f'your answer: {answers[prev_index]}\n\n'
        question_num = i + 1    # question number to show
        if i in range(len(questions)):
            text += f'{question_num}. {questions[i][0]}\n'
        else:
            text += calculate_result(data)
    return text


def update_answers(callback_str: str, data: Dict[str, Any]) -> List[str]:
    answers = data['answers']
    prev_ind = data['current_index'] - 1
    options = data['questions'][prev_ind][1]
    answers[prev_ind] = convert_callback_to_answer(callback_str, options)
    return answers


def convert_callback_to_answer(callback_str: str, options: List[str]) -> str:
    callback_hash = int(callback_str.split('_')[1])
    for option in options:
        if hash(option) == callback_hash:
            return option


def calculate_result(data: Dict[str, Any]) -> str:
    questions = data['questions']
    answers = data['answers']
    correct = 0
    size = len(answers)
    for i in range(size):
        if questions[i][2] == answers[i]:
            correct += 1
    return f'your result is {correct} out of {size} or {(correct / size) * 100}%'
