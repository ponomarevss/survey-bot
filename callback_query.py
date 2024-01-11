import random
import uuid

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from controller import compose_text, update_answers
from keyboards.form_keyboards import get_answers_ikb, get_start_survey_ikb
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


async def unknown_message_handler(message: Message):
    await message.reply(
        text='Unknown message. Use buttons to continue current session or command "/start" to start new one.'
    )


async def incorrect_button_usage_callback_handler(callback: CallbackQuery):
    text = callback.message.text
    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer("Incorrect button usage.")
