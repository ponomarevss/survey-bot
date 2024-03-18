import random
import time
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from admin import ADMIN_ID
from source import tech_questions_source, TECH_QUIZ_SIZE, OPTIONS_NUM, psycho_questions_source
from states import Form


async def command_start_message_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await save_user_data(message, state)
    await state.set_state(Form.s_user_first_name)

    await message.answer(
        text=f'Добро пожаловать!\n'
             f'Это бот для интервью, в рамках которого, ты расскажешь о себе, '
             f'пройдешь небольшой психологичекий и технический тесты.\n'
             f'Ознакомься с "положением об обработке персональных данных" и начнем.\n\n'
             f'Пожалуйста, <b>введи свое имя:</b>',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Положение об обработке персональных данных',
                                         url='https://t.me/gaga_games'),

                ]
            ]
        )
    )


async def first_name_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_user_last_name)
    dict_data = await state.update_data(s_user_first_name=message.text)
    await message.answer(f"Имя: <b>{dict_data['s_user_first_name']}</b>\n"
                         f"Теперь введи свою фамилию.")


async def last_name_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey1)

    dict_data = await state.update_data(s_user_last_name=message.text)

    await message.answer(
        f"Респондент: <b>{dict_data['s_user_first_name']} {dict_data['s_user_last_name']}</b>\n"
        f"Расскажи о себе (не более 1000 символов)."
    )


async def survey1_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey2)

    await state.update_data(s_survey1=message.text)
    await message.answer(
        "Твои лучшие качества (не более 1000 символов)"
    )


async def survey2_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey3)

    await state.update_data(s_survey2=message.text)
    await message.answer(
        "Твои худшие качества (не более 1000 символов)"
    )


async def survey3_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey4)

    await state.update_data(s_survey3=message.text)
    await message.answer(
        "Образование (не более 1000 символов)"
    )


async def survey4_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey5)

    await state.update_data(s_survey4=message.text)
    await message.answer(
        "Опыт работы (не более 1000 символов)"
    )


async def survey5_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey6)

    await state.update_data(s_survey5=message.text)
    await message.answer(
        "Почему решил заняться разработкой ботов? (не более 1000 символов)"
    )


async def survey6_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_survey7)

    await state.update_data(s_survey6=message.text)
    await message.answer(
        "Какое развитие для себя видишь через 1 год (не более 1000 символов)"
    )


async def survey7_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.s_user_phone_num)

    await state.update_data(s_survey7=message.text)

    s_user_phone_num = '+7'
    dict_data = await state.update_data(s_user_phone_num=s_user_phone_num)

    await message.answer(
        f"Благодарю за ответы, <b>{dict_data['s_user_first_name']}</b>.\n"
        f"Теперь, пожалуйста, введи свой номер телефона, начиная со второй цифры.\n"
        f"Телефон: <b>{s_user_phone_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def phone_input_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()
    s_updated_num = dict_data['s_user_phone_num'] + callback.data.split('_')[1]
    dict_data = await state.update_data(s_user_phone_num=s_updated_num)
    await callback.message.edit_text(
        f"Респондент: <b>{dict_data['s_user_first_name']} {dict_data['s_user_last_name']}</b>\n"
        f"Телефон: <b>{s_updated_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def phone_backspace_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()
    s_updated_num = dict_data['s_user_phone_num'][:-1]
    dict_data = await state.update_data(s_user_phone_num=s_updated_num)

    await callback.message.edit_text(
        f"Респондент: <b>{dict_data['s_user_first_name']} {dict_data['s_user_last_name']}</b>\n"
        f"Телефон: <b>{s_updated_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


async def psycho_init_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.list_psycho_answers)

    psycho_questions_dict = create_psycho_questions_dict()
    dict_data = await state.update_data(
        data=psycho_questions_dict,
        i_size=len(psycho_questions_source),
        i_step=0
    )

    await callback.message.edit_text(
        text="Сейчас будет несколько вопросов в рамках психологического тестирования. "
             "Нажми кнопку 'Начать тест', когда будешь готов.",
        reply_markup=get_start_survey_ikb(dict_data)
    )


async def psycho_start_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    await callback.message.edit_text(text=compose_psycho_text(dict_data),
                                     reply_markup=get_psycho_answers_ikb(dict_data))
    await state.update_data(i_step=dict_data['i_step'] + 1)


async def psycho_ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    dict_data = await state.update_data(data=convert_callback_to_psycho_reply(callback.data, dict_data))

    i_step = dict_data['i_step']
    i_size = dict_data['i_size']

    await callback.message.edit_text(text=compose_psycho_text(dict_data),
                                     reply_markup=get_psycho_answers_ikb(dict_data))
    await state.update_data(i_step=i_step + 1)

    if i_step >= i_size:
        dict_data = await state.update_data(dict_psycho_result=calculate_psycho_result(dict_data))
        s_text = callback.message.text + f"\n\n{present_psycho_result(dict_data)}"
        await callback.message.edit_text(s_text)
        await tech_init_callback_handler(callback, state)


async def tech_init_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.list_tech_answers)

    list_questions = get_questions_from_source(TECH_QUIZ_SIZE)
    tech_questions_dict = create_tech_questions_dict(list_questions)
    dict_data = await state.update_data(
        data=tech_questions_dict,
        i_size=TECH_QUIZ_SIZE,
        i_step=1
    )

    await callback.message.answer(
        text="Мы подошли к техническому тестированию. Нажми кнопку 'Начать тест', когда будешь готов.",
        reply_markup=get_start_survey_ikb(dict_data)
    )


async def tech_start_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    await callback.message.edit_text(compose_tech_text(dict_data), reply_markup=get_tech_answers_ikb(dict_data))
    await state.update_data(i_step=dict_data['i_step'] + 1)


async def tech_ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()

    dict_data = await state.update_data(data=convert_callback_to_tech_answer(callback.data, dict_data))
    dict_data = await state.update_data(i_result=calculate_tech_result(dict_data))

    await callback.message.edit_text(compose_tech_text(dict_data), reply_markup=get_tech_answers_ikb(dict_data))

    i_step = dict_data['i_step']
    i_size = dict_data['i_size']

    if i_step <= i_size:
        await state.update_data(i_step=i_step + 1)
    else:
        await callback.message.answer(text=f"{dict_data['s_user_first_name']}, благодарю за потраченное время. "
                                           f"Мы обязательно ознакомимся с результатами твоего тестирования"
                                           f"и перезвоним по оставленному тобой телефону, если они нас заинтересуют.")
        await state.set_state(None)
        await callback.bot.send_message(chat_id=ADMIN_ID[0], text=f'{compose_report(dict_data)}')


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
                InlineKeyboardButton(text="Начать тест", callback_data=f'start_survey_{s_message_id}')
            ]
        ]
    )


def get_psycho_answers_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    s_message_id = v_in_dict_data['s_message_id']

    i_step = v_in_dict_data['i_step']
    i_size = v_in_dict_data['i_size']

    builder = InlineKeyboardBuilder()

    if i_step < i_size:
        for i in range(OPTIONS_NUM):
            s_psycho_option_key = 's_psycho_option' + str(i_step * OPTIONS_NUM + i)
            s_psycho_option = v_in_dict_data[s_psycho_option_key]

            s_callback_data = f"reply_{hash(s_psycho_option[1])}_{s_message_id}"
            builder.button(text=s_psycho_option[1], callback_data=s_callback_data)
    return builder.adjust(1).as_markup()


def get_tech_answers_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    s_message_id = v_in_dict_data['s_message_id']

    i_step = v_in_dict_data['i_step']
    i_size = v_in_dict_data['i_size']

    builder = InlineKeyboardBuilder()

    if i_step <= i_size:
        for i_key_position_index in range(1, OPTIONS_NUM + 1):
            s_answer_key = 's_answer' + str((i_step - 1) * OPTIONS_NUM + i_key_position_index)
            s_answer = v_in_dict_data[s_answer_key]

            s_callback_data = f"ans_{hash(s_answer)}_{s_message_id}"
            builder.button(text=s_answer, callback_data=s_callback_data)
    return builder.adjust(1).as_markup()


# TODO utils
def compose_psycho_text(v_in_dict_data: Dict[str, Any]) -> str:
    s_user_name = f"{v_in_dict_data['s_user_first_name']} {v_in_dict_data['s_user_last_name']}"
    s_text = f'Респондент {s_user_name}:\nПсихологическое тестирование\n\n'

    i_step = v_in_dict_data['i_step']
    i_size = v_in_dict_data['i_size']
    for i in range(i_step + 1):
        if i > 0:
            s_psycho_user_reply_key = 's_psycho_user_reply' + str(i - 1)
            s_psycho_user_reply = v_in_dict_data[s_psycho_user_reply_key]
            s_text += f'Ответ: {s_psycho_user_reply[1]}\n\n'
        if i < i_size:
            s_psycho_question_key = 's_psycho_question' + str(i)
            s_psycho_question = v_in_dict_data[s_psycho_question_key]
            s_text += f'{i + 1}. {s_psycho_question[1]}\n'
    return s_text


def compose_tech_text(v_in_dict_data: Dict[str, Any]) -> str:
    s_user_name = f"{v_in_dict_data['s_user_first_name']} {v_in_dict_data['s_user_last_name']}"
    s_text = f'Респондент {s_user_name}:\nТехническое тестирование\n\n'

    i_step = v_in_dict_data['i_step']
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
            s_text += present_tech_result(v_in_dict_data)
    return s_text


def convert_callback_to_psycho_reply(v_in_s_callback: str, v_in_dict_data: Dict[str, Any]) -> dict:
    i_callback_hash = int(v_in_s_callback.split('_')[1])
    i_step = v_in_dict_data['i_step']
    i_previous_step = i_step - 1
    s_psycho_user_reply_key = 's_psycho_user_reply' + str(i_previous_step)

    for i in range(i_previous_step * OPTIONS_NUM, i_step * OPTIONS_NUM):
        s_psycho_option_key = 's_psycho_option' + str(i)
        s_psycho_option = v_in_dict_data[s_psycho_option_key]
        if hash(s_psycho_option[1]) == i_callback_hash:
            return {s_psycho_user_reply_key: s_psycho_option}


def convert_callback_to_tech_answer(v_in_s_callback: str, v_in_dict_data: Dict[str, Any]) -> dict:
    i_callback_hash = int(v_in_s_callback.split('_')[1])

    i_previous_step = v_in_dict_data['i_step'] - 1
    s_state_key = 's_state' + str(i_previous_step)

    for i in range(i_previous_step * OPTIONS_NUM - (OPTIONS_NUM - 1), i_previous_step * OPTIONS_NUM + 1):
        s_answer_key = 's_answer' + str(i)
        s_answer = v_in_dict_data[s_answer_key]
        if hash(s_answer) == i_callback_hash:
            return {s_state_key: s_answer}


def calculate_psycho_result(v_in_dict_data: Dict[str, Any]) -> dict:
    i_size = v_in_dict_data['i_size']
    dict_result = dict()
    for i in range(i_size):
        s_psycho_question_key = 's_psycho_question' + str(i)
        s_psycho_question = v_in_dict_data[s_psycho_question_key]

        s_psycho_user_reply_key = 's_psycho_user_reply' + str(i)
        s_psycho_user_reply = v_in_dict_data[s_psycho_user_reply_key]

        if s_psycho_question[0] in dict_result.keys():
            dict_result[s_psycho_question[0]] += s_psycho_user_reply[0]
        else:
            dict_result[s_psycho_question[0]] = s_psycho_user_reply[0]
    return dict_result


def calculate_tech_result(v_in_dict_data: Dict[str, Any]) -> int:
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


def present_psycho_result(v_in_dict_data: Dict[str, Any]) -> str:
    dict_psycho_result = v_in_dict_data['dict_psycho_result']
    list_sorted_result = sorted(dict_psycho_result.items(), key=lambda item: item[1], reverse=True)
    s_result = f'Результат психологического тестирования: '
    for tuple_result in list_sorted_result:
        s_result += f'{tuple_result[0]} {tuple_result[1]}, '
    return s_result[:-2]


def present_tech_result(v_in_dict_data: Dict[str, Any]) -> str:
    i_size = v_in_dict_data['i_size']
    i_correct = v_in_dict_data['i_result']
    s_result = f'Результат технического тестирования: {i_correct} из {i_size} или {(i_correct / i_size) * 100}%'
    return s_result


def compose_report(v_in_dict_data: Dict[str, Any]) -> str:
    return (f"Респондент: {v_in_dict_data['s_user_first_name']} {v_in_dict_data['s_user_last_name']}\n"
            f"Телефон: {v_in_dict_data['s_user_phone_num']}\n"
            f"О себе: {v_in_dict_data['s_survey1']}\n"
            f"Лучшие качества: {v_in_dict_data['s_survey2']}\n"
            f"Худшие качества: {v_in_dict_data['s_survey3']}\n"
            f"Образование: {v_in_dict_data['s_survey4']}\n"
            f"Опыт работы: {v_in_dict_data['s_survey5']}\n"
            f"Почему решил: {v_in_dict_data['s_survey6']}\n"
            f"Какое развитие через 1 год: {v_in_dict_data['s_survey7']}\n"
            f"{present_psycho_result(v_in_dict_data)}\n"
            f"Результат технического тестирования: {v_in_dict_data['i_result']} из {v_in_dict_data['i_size']} или "
            f"{(v_in_dict_data['i_result'] / v_in_dict_data['i_size']) * 100}%")


def get_questions_from_source(i_size: int) -> list[tuple[str, list[str], str]]:
    return random.sample(tech_questions_source, i_size)


def create_tech_questions_dict(v_in_list_questions: list[tuple[str, list[str], str]]) -> Dict[str, Any]:
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


def create_psycho_questions_dict() -> Dict[str, Any]:
    dict_result = dict()
    for i in range(len(psycho_questions_source)):
        s_psycho_question_key = 's_psycho_question' + str(i)
        s_psycho_question_value = psycho_questions_source[i][0], psycho_questions_source[i][1]
        dict_result[s_psycho_question_key] = s_psycho_question_value

        s_psycho_user_reply_key = 's_psycho_user_reply' + str(i)
        dict_result[s_psycho_user_reply_key] = ''

        i_options = len(psycho_questions_source[i][2])
        for j in range(i_options):
            s_psycho_option_key = 's_psycho_option' + str(i * i_options + j)
            s_psycho_option_value = psycho_questions_source[i][2][j]
            dict_result[s_psycho_option_key] = s_psycho_option_value
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
