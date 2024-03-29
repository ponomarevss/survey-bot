import random
import time
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from source import questions_source
from states import Form


async def command_start_message_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка команды '/start'.

    :param message:
    :param state:
    :return:
    """
    await state.clear()
    await save_user_data(message, state)  # запись данных пользователя в хранилище FSMContext
    await state.set_state(Form.s_user_name)  # установка активного состояния FSMContext

    s_text = (f"Добро пожаловать! Это бот для теста знаний.\n"
              f"Как я могу к вам обращаться? (Введите свое имя)")
    await message.answer(text=s_text)


async def init_state_message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.list_answers)  # установка активного состояния FSMContext

    i_size = 10  # размер вопросника
    list_questions = get_questions_from_source(i_size)  # получение вопросов из источника
    dict_data = await state.update_data(
        data=create_questions_dict(list_questions),  # добавление словаря с вопросами и ответами
        s_user_name=message.text,  # имя респондента
        i_size=i_size,  # количество вопросов
        i_st_step=1,  # номер шага
    )

    s_text = (f"{dict_data['s_user_name']}, давайте начнем наш тест.\n"
              f"Нажмите кнопку 'Начать тест', когда будете готовы.")
    await message.answer(text=s_text, reply_markup=get_start_survey_ikb(dict_data))


async def unknown_message_handler(message: Message):
    """
    Обработка некорректного текстового сообщения.

    :param message:
    :return:
    """
    await message.reply(
        text='Некорректное текстовое сообщение.\n'
             'Используйте предложенные кнопки для продолжения теста или команду "/start" для запуска новой сессии.'
    )


async def start_survey_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка коллбэка начала теста. Задача:
    - проверить коллбэк на соответствие текущему session_id;
    - в случае успеха, вывести на экран первый вопрос и клавиатуру с вариантами ответов;
    - в случае провала, выполнить действия, связанные с некорректным использованием кнопок.

    :param callback:
    :param state:
    :return:
    """
    dict_data = await state.get_data()  # получение данных из FSMContext хранилища

    # проверка эквивалентности session_id полученному из коллбэка
    if dict_data['s_message_id'] == callback.data.split('_')[2]:
        # вывод вопроса и клавиатуры с вариантами ответа
        await callback.message.edit_text(compose_text(dict_data), reply_markup=get_answers_ikb(dict_data))

        await state.update_data(i_st_step=dict_data['i_st_step'] + 1)  # инкремент текущего шага в FSMContext хранилище
    else:
        # выполнение действий, связанных с некорректным использованием кнопок
        await incorrect_button_usage_callback_handler(callback)


async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    dict_data = await state.get_data()  # получение данных из FSMContext хранилища

    # проверка эквивалентности s_message_id полученному из коллбэка
    if dict_data['s_message_id'] == callback.data.split('_')[2]:

        # сохранение ответа пользователя с предыдущего шага
        dict_data = await state.update_data(data=convert_callback_to_user_answer(callback.data, dict_data))

        await callback.message.edit_text(compose_text(dict_data), reply_markup=get_answers_ikb(dict_data))

        i_step = dict_data['i_st_step']  # текущий шаг
        i_size = dict_data['i_size']  # количество вопросов

        # проверка текущего шага:
        if i_step <= i_size:
            await state.update_data(i_st_step=dict_data['i_st_step'] + 1)  # инкремент текущего индекса в FSMContext
        else:
            await state.set_state(None)  # сброс активного состояния FSMContext

    else:
        # выполнение действий, связанных с некорректным использованием кнопок
        await incorrect_button_usage_callback_handler(callback)


async def incorrect_button_usage_callback_handler(callback: CallbackQuery):
    """
    Обработка коллбэка ответов на вопросы. У сообщения сохраняется текст, но удаляется клавиатура.

    :param callback:
    :return:
    """
    await callback.message.edit_text(text=callback.message.text, reply_markup=None)
    await callback.answer("Некорректное использование кнопки.")


def get_start_survey_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры для начала теста. Формирование коллбэка с s_message_id.

    :param v_in_dict_data:
    :return:
    """
    s_message_id = v_in_dict_data['s_message_id']  # получение s_message_id из FSM
    s_callback_data = f'start_survey_{s_message_id}'  # формирование коллбэка с s_message_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать тест", callback_data=s_callback_data)]
        ]
    )


def get_answers_ikb(v_in_dict_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры с вариантами ответа, либо None, если текущий индекс за пределами листа вопросов.
    Формирование коллбэков на основе префикса "ans", хэш значения варианта ответа и s_message_id.

    :param v_in_dict_data:
    :return:
    """
    s_message_id = v_in_dict_data['s_message_id']  # s_message_id как идентификатор текущей сессии

    i_step = v_in_dict_data['i_st_step']  # текущий шаг
    i_size = v_in_dict_data['i_size']  # количество вопросов

    list_buttons = list()  # список кнопок
    ikb = None  # начальное значение клавиатуры

    # проверка индекса на вхождение в лист вопросов
    if i_step <= i_size:
        for i_key_position_index in range(1, 5):  # i_key_position_index = 1 ... 4
            s_answer_key = 's_answer' + str((i_step - 1) * 4 + i_key_position_index)
            s_answer = v_in_dict_data[s_answer_key]

            s_callback_data = f"ans_{hash(s_answer)}_{s_message_id}"  # коллбэк с хэш варианта ответа и s_message_id
            list_buttons.append(InlineKeyboardButton(text=s_answer, callback_data=s_callback_data))

        # формирование клавиатуры 2 на 2
        ikb = InlineKeyboardMarkup(inline_keyboard=[list_buttons[:2], list_buttons[2:]])
    return ikb


def compose_text(v_in_dict_data: Dict[str, Any]) -> str:
    """
    Формирование текста сообщения на основе данных FSM.
    Если вопрос первый, будет выведен только текст первого вопроса.
    Для последующих вопросов, сначала будет выведены предыдущие вопросы с ответами.
    Для последнего вопроса, список вопросов и полученных ответов будет дополнен результатом теста.

    :param v_in_dict_data:
    :return:
    """
    s_user_name = v_in_dict_data['s_user_name']
    s_text = f'Тестирование кандидата {s_user_name}:\n\n'  # часть текста с обращением

    i_step = v_in_dict_data['i_st_step']  # текущий шаг
    i_size = v_in_dict_data['i_size']  # количество вопросов

    # цикл с формированием текста для элементов списка вопросов и ответов от 0 до текущего
    for i in range(1, i_step + 1):  # i_step = 1 ... 10
        i_previous_step = i - 1  # индекс ответа на предыдущий вопрос
        if i_previous_step > 0:
            s_state_key = 's_state' + str(i_previous_step)
            s_text += f'Ответ: {v_in_dict_data[s_state_key]}\n\n'  # добавление ответа на предыдущий вопрос

        if i <= i_size:
            s_question_key = 's_question' + str(i)  # ключ для вопроса
            s_question = v_in_dict_data[s_question_key]  # вопрос из FSMContext хранилища
            s_text += f'{i}. {s_question}\n'  # добавление текущего вопроса
        else:
            s_text += calculate_result(v_in_dict_data)  # вывод результата теста
    return s_text


def convert_callback_to_user_answer(v_in_s_callback: str, v_in_dict_data: Dict[str, Any]) -> dict:
    """
    Конвертирование хэш значения ответа, полученного из коллбэка.
    Хэш сравнивается с хэшированными значениями элементов передаваемого в функцию списка.

    :param v_in_s_callback:
    :param v_in_dict_data:
    :return:
    """
    i_callback_hash = int(v_in_s_callback.split('_')[1])  # хэш ответа из коллбэка

    i_previous_step = v_in_dict_data['i_st_step'] - 1  # номер предыдущего шага
    s_state_key = 's_state' + str(i_previous_step)  # ключ для ответа пользователя

    for i in range(i_previous_step * 4 - 3, i_previous_step * 4 + 1):
        s_answer_key = 's_answer' + str(i)
        s_answer = v_in_dict_data[s_answer_key]
        if hash(s_answer) == i_callback_hash:
            return {s_state_key: s_answer}


def calculate_result(v_in_dict_data: Dict[str, Any]) -> str:
    """
    Подсчет результатов теста на основе данных из FSM.

    :param v_in_dict_data:
    :return:
    """

    i_correct = 0  # счетчик правильных ответов
    i_size = v_in_dict_data['i_size']  # количество вопросов

    for i in range(1, i_size + 1):
        s_state_key = 's_state' + str(i)  # ключ для ответа пользователя
        s_state = v_in_dict_data[s_state_key]  # ответа пользователя из FSMContext хранилища

        s_recommendation_key = 's_recommendation' + str(i)  # ключ для ответа
        s_recommendation = v_in_dict_data[s_recommendation_key]  # ответ из FSMContext хранилища

        if s_state == s_recommendation:
            i_correct += 1

    # предоставляется строка с результатом
    return f'Результат: {i_correct} из {i_size} или {(i_correct / i_size) * 100}%'


def get_questions_from_source(i_size: int) -> list[tuple[str, list[str], str]]:
    """
    Формирование списка вопросов размером size из источника.
    Формат объекта вопроса: (текст вопроса, [варианты ответов], правильный ответ).

    :param i_size:
    :return:
    """
    return random.sample(questions_source, i_size)


def create_questions_dict(v_in_list_questions: list[tuple[str, list[str], str]]) -> Dict[str, Any]:
    """
    Формирование словаря с ключами:
        s_state#            - вариант ответа пользователя
        s_answer#           - вариант ответа
        s_recommendation#   - правильный ответ
        s_question#         - вопрос
    и заполнение его данными из листа с tuple[str, list[str], str]

    :param v_in_list_questions:
    :return:
    """

    dict_result = dict()
    for i_list_questions_index in range(len(v_in_list_questions)):
        # нумерация полей s_question# и s_recommendation# в StateTestAnswer начинается с 1
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
            # нумерация полей s_answer# в StateTestAnswer начинается с 1
            i_k = i_list_answers_index + 1

            s_answer_key = 's_answer' + str(i_list_questions_index * 4 + i_k)
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
