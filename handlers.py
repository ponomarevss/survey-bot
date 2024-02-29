from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from admin import ADMIN_ID
from keyboards import get_phone_input_ikb, get_start_survey_ikb, get_psycho_answers_ikb, get_tech_answers_ikb
from source import TECH_QUIZ_SIZE, psycho_questions_source
from states import Form
from utils import save_user_data, save_message_to_t_log, create_psycho_questions_dict, save_callback_to_t_log, \
    compose_psycho_text, convert_callback_to_psycho_reply, calculate_psycho_result, present_psycho_result, \
    get_questions_from_source, create_tech_questions_dict, compose_tech_text, convert_callback_to_tech_answer, \
    calculate_tech_result, compose_report


async def command_start_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.clear()
    await save_user_data(message, state, session)
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


async def first_name_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_user_last_name)
    dict_data = await state.update_data(s_user_first_name=message.text)
    await save_message_to_t_log(message, 'Пожалуйста, введи свое имя', session)
    await message.answer(f"Имя: <b>{dict_data['s_user_first_name']}</b>\n"
                         f"Теперь введи свою фамилию.")


async def last_name_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey1)

    dict_data = await state.update_data(s_user_last_name=message.text)
    await save_message_to_t_log(message, 'Теперь введи свою фамилию', session)

    await message.answer(
        f"Респондент: <b>{dict_data['s_user_first_name']} {dict_data['s_user_last_name']}</b>\n"
        f"Расскажи о себе (не более 1000 символов)."
    )


async def survey1_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey2)

    await save_message_to_t_log(message, 'Расскажи о себе (не более 1000 символов)', session)

    await state.update_data(s_survey1=message.text)

    await message.answer(
        "Твои лучшие качества (не более 1000 символов)"
    )


async def survey2_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey3)

    await save_message_to_t_log(message, 'Твои лучшие качества (не более 1000 символов)', session)

    await state.update_data(s_survey2=message.text)
    await message.answer(
        "Твои худшие качества (не более 1000 символов)"
    )


async def survey3_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey4)

    await save_message_to_t_log(message, 'Твои худшие качества (не более 1000 символов)', session)

    await state.update_data(s_survey3=message.text)
    await message.answer(
        "Образование (не более 1000 символов)"
    )


async def survey4_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey5)

    await save_message_to_t_log(message, 'Образование (не более 1000 символов)', session)

    await state.update_data(s_survey4=message.text)
    await message.answer(
        "Опыт работы (не более 1000 символов)"
    )


async def survey5_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey6)

    await save_message_to_t_log(message, 'Опыт работы (не более 1000 символов)', session)

    await state.update_data(s_survey5=message.text)
    await message.answer(
        "Почему решил заняться разработкой ботов? (не более 1000 символов)"
    )


async def survey6_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_survey7)

    await save_message_to_t_log(
        message, 'Почему решил заняться разработкой ботов? (не более 1000 символов)', session
    )

    await state.update_data(s_survey6=message.text)
    await message.answer(
        "Какое развитие для себя видишь через 1 год (не более 1000 символов)"
    )


async def survey7_message_handler(message: Message, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.s_user_phone_num)

    await save_message_to_t_log(message, 'Какое развитие для себя видишь через 1 год (не более 1000 символов)', session)

    await state.update_data(s_survey7=message.text)

    s_user_phone_num = '+79998887766'
    dict_data = await state.update_data(s_user_phone_num=s_user_phone_num)

    await message.answer(
        f"Благодарю за ответы, <b>{dict_data['s_user_first_name']}</b>.\n"
        f"Теперь, пожалуйста, введи свой номер телефона, начиная со второй цифры.\n"
        f"Телефон: <b>{s_user_phone_num}</b>",
        reply_markup=get_phone_input_ikb(dict_data)
    )


# TODO: callback handlers
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


async def psycho_init_callback_handler(callback: CallbackQuery, state: FSMContext, session: Session) -> None:
    await state.set_state(Form.list_psycho_answers)

    psycho_questions_dict = create_psycho_questions_dict()
    dict_data = await state.update_data(
        data=psycho_questions_dict,
        i_size=len(psycho_questions_source),
        i_step=0
    )

    await save_callback_to_t_log(callback, 'Телефон', dict_data['s_user_phone_num'], session)

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
