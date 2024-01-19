import random
import time
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from source import questions_source, QUIZ_SIZE, OPTIONS_NUM
from states import Form


async def command_start_message_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await save_user_data(message, state)
    await state.set_state(Form.s_user_first_name)

    await message.answer(f'Добро пожаловать! Это бот для теста знаний.\n'
                         f'Пожалуйста, введите свое имя.')


async def first_name_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_user_last_name)
    dict_data = await state.update_data(s_user_first_name=message.text)
    await message.answer(f"Ваше имя: {dict_data['s_user_first_name']}.\n"
                         f"Теперь введите свою фамилию.")


async def last_name_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_user_phone_num)

    s_user_phone_num = '+7'
    dict_data = await state.update_data(s_user_last_name=message.text, s_user_phone_num=s_user_phone_num)

    await message.answer(
        f"{dict_data['s_user_first_name']} {dict_data['s_user_last_name']},\n"
        f"введите, пожалуйста, свой номер телефона, начиная со второй цифры.\n"
        f"Телефон: <b>{s_user_phone_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def phone_input_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()
    s_updated_num = dict_data['s_user_phone_num'] + callback.data.split('_')[1]
    dict_data = await state.update_data(s_user_phone_num=s_updated_num)

    await callback.message.edit_text(
        f"Респондент: {dict_data['s_user_first_name']} {dict_data['s_user_last_name']}\n"
        f"Телефон: <b>{s_updated_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def phone_backspace_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()
    s_updated_num = dict_data['s_user_phone_num'][:-1]
    dict_data = await state.update_data(s_user_phone_num=s_updated_num)

    await callback.message.edit_text(
        f"Респондент: {dict_data['s_user_first_name']} {dict_data['s_user_last_name']}\n"
        f"Телефон: <b>{s_updated_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def init_quiz_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.list_answers)

    list_questions = get_questions_from_source(QUIZ_SIZE)
    dict_data = await state.update_data(data=create_questions_dict(list_questions), i_size=QUIZ_SIZE, i_st_step=1)

    s_text = (f"Респондент: {dict_data['s_user_first_name']} {dict_data['s_user_last_name']}\n"
              f"Ознакомьтесь с 'положением об обработке персональных данных', "
              f"затем нажмите кнопку 'Начать тест', когда будете готовы.")
    await callback.message.edit_text(text=s_text, reply_markup=get_start_survey_ikb(dict_data))


async def start_survey_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    await callback.message.edit_text(compose_text(dict_data), reply_markup=get_answers_ikb(dict_data))
    await state.update_data(i_st_step=dict_data['i_st_step'] + 1)


async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    dict_data = await state.update_data(data=convert_callback_to_user_answer(callback.data, dict_data))
    dict_data = await state.update_data(i_result=calculate_result(dict_data))

    await callback.message.edit_text(compose_text(dict_data), reply_markup=get_answers_ikb(dict_data))

    i_step = dict_data['i_st_step']
    i_size = dict_data['i_size']

    if i_step <= i_size:
        await state.update_data(i_st_step=i_step + 1)
    else:
        await state.set_state(None)


async def unknown_message_handler(message: Message):
    await message.reply(
        text='Некорректное текстовое сообщение.\n'
             'Используйте предложенные кнопки для продолжения теста или команду "/start" для запуска новой сессии.'
    )


def get_phone_input_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    s_message_id = v_in_dict_data['s_message_id']

    list_buttons = list()
    for i in range(0, 10):
        s_callback_data = f'phone_{i}_{s_message_id}'
        list_buttons.append(InlineKeyboardButton(text=f'{i}', callback_data=s_callback_data))

    backspace_button = InlineKeyboardButton(text='<-', callback_data=f'backspace_button_{s_message_id}')
    confirm_button = InlineKeyboardButton(text='OK', callback_data=f'confirm_button_{s_message_id}')

    i_length = len(v_in_dict_data['s_user_phone_num'])
    ikb_markup = InlineKeyboardMarkup(inline_keyboard=[list_buttons[1:4], list_buttons[4:7], list_buttons[7:]])
    if i_length == 2:
        ikb_markup.inline_keyboard.append([list_buttons[0]])
    elif i_length >= 12:
        ikb_markup.inline_keyboard.clear()
        ikb_markup.inline_keyboard.append([backspace_button, confirm_button])
    else:
        ikb_markup.inline_keyboard.append([backspace_button, list_buttons[0]])
    return ikb_markup


def get_start_survey_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    s_message_id = v_in_dict_data['s_message_id']
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Положение об обработке персональных данных', url='https://t.me/gaga_games'),
                InlineKeyboardButton(text="Начать тест", callback_data=f'start_survey_{s_message_id}')
            ]
        ]
    )


def get_answers_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    s_message_id = v_in_dict_data['s_message_id']

    i_step = v_in_dict_data['i_st_step']
    i_size = v_in_dict_data['i_size']

    list_buttons = list()
    ikb = None

    if i_step <= i_size:
        for i_key_position_index in range(1, OPTIONS_NUM + 1):
            s_answer_key = 's_answer' + str((i_step - 1) * OPTIONS_NUM + i_key_position_index)
            s_answer = v_in_dict_data[s_answer_key]

            s_callback_data = f"ans_{hash(s_answer)}_{s_message_id}"
            list_buttons.append(InlineKeyboardButton(text=s_answer, callback_data=s_callback_data))

        ikb = InlineKeyboardMarkup(
            inline_keyboard=[list_buttons[:2], list_buttons[2:4], list_buttons[4:6], [list_buttons[6]]]
        )
    return ikb


def compose_text(v_in_dict_data: Dict[str, Any]) -> str:
    s_user_name = f"{v_in_dict_data['s_user_first_name']} {v_in_dict_data['s_user_last_name']}"
    s_text = f'Респондент {s_user_name}:\n\n'

    i_step = v_in_dict_data['i_st_step']
    i_size = v_in_dict_data['i_size']

    for i in range(1, i_step + 1):
        i_previous_step = i - 1
        if i_previous_step > 0:
            s_state_key = 's_state' + str(i_previous_step)
            s_text += f'Ответ: {v_in_dict_data[s_state_key]}\n\n'

        if i <= i_size:
            s_question_key = 's_question' + str(i)
            s_question = v_in_dict_data[s_question_key]
            s_text += f'{i}. {s_question}\n'
        else:
            s_text += present_result(v_in_dict_data)
    return s_text


def convert_callback_to_user_answer(v_in_s_callback: str, v_in_dict_data: Dict[str, Any]) -> dict:
    i_callback_hash = int(v_in_s_callback.split('_')[1])

    i_previous_step = v_in_dict_data['i_st_step'] - 1
    s_state_key = 's_state' + str(i_previous_step)

    for i in range(i_previous_step * OPTIONS_NUM - (OPTIONS_NUM - 1), i_previous_step * OPTIONS_NUM + 1):
        s_answer_key = 's_answer' + str(i)
        s_answer = v_in_dict_data[s_answer_key]
        if hash(s_answer) == i_callback_hash:
            return {s_state_key: s_answer}


def calculate_result(v_in_dict_data: Dict[str, Any]) -> int:
    i_correct = 0
    i_size = v_in_dict_data['i_size']

    for i in range(1, i_size + 1):
        s_state_key = 's_state' + str(i)
        s_state = v_in_dict_data[s_state_key]

        s_recommendation_key = 's_recommendation' + str(i)
        s_recommendation = v_in_dict_data[s_recommendation_key]

        if s_state == s_recommendation:
            i_correct += 1
    return i_correct


def present_result(v_in_dict_data: Dict[str, Any]) -> str:
    i_size = v_in_dict_data['i_size']
    i_correct = v_in_dict_data['i_result']
    s_user_first_name = v_in_dict_data['s_user_first_name']
    s_user_last_name = v_in_dict_data['s_user_last_name']
    s_user_phone_num = v_in_dict_data['s_user_phone_num']
    s_result = f'Результат: {i_correct} из {i_size} или {(i_correct / i_size) * 100}%'
    print(f"Респондент: {s_user_first_name} {s_user_last_name}\n"
          f"Телефон: {s_user_phone_num}\n"
          f"{s_result}")
    return s_result


def get_questions_from_source(i_size: int) -> list[tuple[str, list[str], str]]:
    return random.sample(questions_source, i_size)


def create_questions_dict(v_in_list_questions: list[tuple[str, list[str], str]]) -> Dict[str, Any]:
    dict_result = dict()
    for i_list_questions_index in range(len(v_in_list_questions)):
        i_j = i_list_questions_index + 1

        s_question_key = 's_question' + str(i_j)
        s_question_value = v_in_list_questions[i_list_questions_index][0]
        dict_result[s_question_key] = s_question_value

        s_recommendation_key = 's_recommendation' + str(i_j)
        s_recommendation_value = v_in_list_questions[i_list_questions_index][2]
        dict_result[s_recommendation_key] = s_recommendation_value

        s_state_key = 's_state' + str(i_j)
        dict_result[s_state_key] = ''

        for i_list_answers_index in range(len(v_in_list_questions[i_list_questions_index][1])):
            i_k = i_list_answers_index + 1

            s_answer_key = 's_answer' + str(i_list_questions_index * OPTIONS_NUM + i_k)
            s_answer_value = v_in_list_questions[i_list_questions_index][1][i_list_answers_index]
            dict_result[s_answer_key] = s_answer_value
    return dict_result


async def save_user_data(v_in_message, v_in_state):
    dict_data = await v_in_state.update_data(
        s_message_id=str(v_in_message.message_id),
        user_id=v_in_message.from_user.id,
        s_username=v_in_message.from_user.username,
        s_first_name=v_in_message.from_user.first_name,
        s_last_name=v_in_message.from_user.last_name,
        s_language_code=v_in_message.from_user.language_code,
        s_is_premium=v_in_message.from_user.is_premium,
        dt_dateupd=time.time()
    )
    print(dict_data)
