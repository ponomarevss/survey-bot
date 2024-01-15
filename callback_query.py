import random
import time
from typing import Dict, Any, List

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
    await state.set_state(Form.list_answers)  # установка активного состояния FSM

    i_size = 10  # размер вопросника
    list_questions = get_questions_from_source(i_size)  # получение вопросов из источника
    data = await state.update_data(
        data=create_questions_dict(list_questions),  # добавление словаря с вопросами и ответами
        s_user_name=message.text,  # имя респондента
        i_size=i_size,  # количество вопросов
        i_st_step=1,  # исходный индекс для обращения к спискам вопросов и ответов
    )

    s_text = (f"{data['s_user_name']}, давайте начнем наш тест.\n"
              f"Нажмите кнопку 'Начать тест', когда будете готовы.")
    await message.answer(text=s_text, reply_markup=get_start_survey_ikb(data))


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
    data = await state.get_data()  # получение данных из FSM

    # проверка эквивалентности session_id полученному из коллбэка
    if data['s_message_id'] == callback.data.split('_')[2]:
        # вывод вопроса и клавиатуры с вариантами ответа
        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        await state.update_data(i_st_step=data['i_st_step'] + 1)  # инкремент текущего индекса в FSM
    else:
        # выполнение действий, связанных с некорректным использованием кнопок
        await incorrect_button_usage_callback_handler(callback)


async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка коллбэка ответов на вопросы. Задача:
    - проверить коллбэк на соответствие текущему s_message_id;
    - в случае провала, выполнить действия, связанные с некорректным использованием кнопок;
    - в случае успеха, выполнить проверку, является ли вопрос последним:
        - если вопрос не последний, отобразить ответ на предыдущий вопрос,
            вывести следующий вопрос и клавиатуру с вариантами ответов;
        - если вопрос последний, отобразить ответ на предыдущий вопрос, отобразить результаты теста.

    :param callback:
    :param state:
    :return:
    """
    data = await state.get_data()  # получение данных из FSM

    # проверка эквивалентности s_message_id полученному из коллбэка
    if data['s_message_id'] == callback.data.split('_')[2]:

        # TODO остановился здесь

        # обновление данных FSM на основе данных коллбэка
        await state.update_data(answers=compose_updated_answers(callback.data, data))

        # в зависимости от того, последний вопрос или нет:
        #   вывод ответа на предыдущий вопрос,
        #   текущего вопроса,
        #   результата теста
        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        current_index = data['current_index']  # получение текущего индекса

        # проверка текущего индекса:
        #   если индекс за пределами листа вопросов, активное сбросить состояние FSM, если нет, выполнить инкремент
        if current_index in range(0, len(data['questions'])):
            await state.update_data(current_index=data['current_index'] + 1)  # инкремент текущего индекса в FSM
        else:
            await state.set_state(None)  # установка активного состояния FSM

    else:

        # выполнение действий, связанных с некорректным использованием кнопок
        await incorrect_button_usage_callback_handler(callback)


# async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
#     """
#     Обработка коллбэка ответов на вопросы. Задача:
#     - проверить коллбэк на соответствие текущему s_message_id;
#     - в случае провала, выполнить действия, связанные с некорректным использованием кнопок;
#     - в случае успеха, выполнить проверку, является ли вопрос последним:
#         - если вопрос не последний, отобразить ответ на предыдущий вопрос,
#             вывести следующий вопрос и клавиатуру с вариантами ответов;
#         - если вопрос последний, отобразить ответ на предыдущий вопрос, отобразить результаты теста.
#
#     :param callback:
#     :param state:
#     :return:
#     """
#     data = await state.get_data()  # получение данных из FSM
#
#     # проверка эквивалентности s_message_id полученному из коллбэка
#     if data['s_message_id'] == callback.data.split('_')[2]:
#
#         # обновление данных FSM на основе данных коллбэка
#         await state.update_data(answers=compose_updated_answers(callback.data, data))
#
#         # в зависимости от того, последний вопрос или нет:
#         #   вывод ответа на предыдущий вопрос,
#         #   текущего вопроса,
#         #   результата теста
#         await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))
#
#         current_index = data['current_index']  # получение текущего индекса
#
#         # проверка текущего индекса:
#         #   если индекс за пределами листа вопросов, активное сбросить состояние FSM, если нет, выполнить инкремент
#         if current_index in range(0, len(data['questions'])):
#             await state.update_data(current_index=data['current_index'] + 1)  # инкремент текущего индекса в FSM
#         else:
#             await state.set_state(None)  # установка активного состояния FSM
#
#     else:
#
#         # выполнение действий, связанных с некорректным использованием кнопок
#         await incorrect_button_usage_callback_handler(callback)
#
#
async def incorrect_button_usage_callback_handler(callback: CallbackQuery):
    """
    Обработка коллбэка ответов на вопросы. У сообщения сохраняется текст, но удаляется клавиатура.

    :param callback:
    :return:
    """
    await callback.message.edit_text(text=callback.message.text, reply_markup=None)
    await callback.answer("Некорректное использование кнопки.")


def get_start_survey_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры для начала теста. Формирование коллбэка с s_message_id.

    :param data:
    :return:
    """
    s_message_id = data['s_message_id']  # получение s_message_id из FSM
    s_callback_data = f'start_survey_{s_message_id}'  # формирование коллбэка с s_message_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать тест", callback_data=s_callback_data)]
        ]
    )


def get_answers_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры с вариантами ответа, либо None, если текущий индекс за пределами листа вопросов.
    Формирование коллбэков на основе префикса "ans", хэш значения варианта ответа и s_message_id.

    :param data:
    :return:
    """
    s_message_id = data['s_message_id']             # s_message_id как идентификатор текущей сессии

    i_step = data['i_st_step']                      # текущий индекс
    i_size = data['i_size']                         # количество вопросов

    list_buttons = list()                           # список кнопок
    ikb = None                                      # начальное значение клавиатуры

    # проверка индекса на вхождение в лист вопросов
    if i_step <= i_size:
        for i_key_position_index in range(1, 5):  # i_key_position_index = 1 ... 4
            s_answer_key = 's_answer' + str((i_step - 1) + i_key_position_index)
            s_answer = data[s_answer_key]

            callback_data = f"ans_{hash(s_answer)}_{s_message_id}"  # коллбэк с хэш варианта ответа и s_message_id
            list_buttons.append(InlineKeyboardButton(text=s_answer, callback_data=callback_data))

        # формирование клавиатуры 2 на 2
        ikb = InlineKeyboardMarkup(inline_keyboard=[list_buttons[:2], list_buttons[2:]])
    return ikb


def compose_text(data: Dict[str, Any]) -> str:
    """
    Формирование текста сообщения на основе данных FSM.
    Если вопрос первый, будет выведен только текст первого вопроса.
    Для последующих вопросов, сначала будет выведены предыдущие вопросы с ответами.
    Для последнего вопроса, список вопросов и полученных ответов будет дополнен результатом теста.

    :param data:
    :return:
    """
    s_user_name = data['s_user_name']
    s_text = f'Тестирование кандидата {s_user_name}:\n\n'   # часть текста с обращением

    i_step = data['i_st_step']                              # текущий индекс
    i_size = data['i_size']                                 # количество вопросов

    # цикл с формированием текста для элементов списка вопросов и ответов от 0 до текущего
    for i in range(1, i_step + 1):                          # i_step = 1 ... 10
        i_previous_step = i - 1                             # индекс ответа на предыдущий вопрос
        if i_previous_step > 0:
            s_answer_key = 's_answer' + str(i_previous_step)
            s_text += f'Ответ: {data[s_answer_key]}\n\n'    # добавление ответа на предыдущий вопрос

        if i <= i_size:
            s_question_key = 's_question' + str(i)          # ключ для вопроса
            s_question = data[s_question_key]               # вопрос из FSMContext хранилища
            s_text += f'{i}. {s_question}\n'                # добавление текущего вопроса
        else:
            s_text += calculate_result(data)                # вывод результата теста
    return s_text


def compose_updated_answers(callback_str: str, data: Dict[str, Any]) -> List[str]:
    """
    Формирование обновленного листа ответов на основе данных FSM и полученного коллбэка.

    :param callback_str:
    :param data:
    :return:
    """
    answers = data['answers']  # список ответов из FSM
    prev_ind = data['current_index'] - 1  # предыдущий индекс
    options = data['questions'][prev_ind][1]  # ответы из (текст вопроса, [варианты ответов], правильный ответ)

    # присвоение нового значения элементу списка ответов на основе коллбэка
    answers[prev_ind] = convert_callback_to_answer(callback_str, options)
    return answers


def convert_callback_to_answer(callback_str: str, options: List[str]) -> str:
    """
    Конвертирование хэш значения ответа, полученного из коллбэка.
    Хэш сравнивается с хэшированными значениями элементов передаваемого в функцию списка.

    :param callback_str:
    :param options:
    :return:
    """
    callback_hash = int(callback_str.split('_')[1])  # хэш ответа из коллбэка

    # поиск совпадения с хэшем варианта ответа из списка
    for option in options:
        if hash(option) == callback_hash:
            return option


def calculate_result(data: Dict[str, Any]) -> str:
    """
    Подсчет результатов теста на основе данных из FSM.

    :param data:
    :return:
    """

    i_correct = 0               # счетчик правильных ответов
    i_size = data['i_size']     # количество вопросов

    # поиск совпадений ответов с правильным из объекта (текст вопроса, [варианты ответов], правильный ответ)
    # с соответствующим инкрементом счетчика правильных ответов
    for i in range(1, i_size + 1):
        s_question_key = 's_question' + str(i)      # ключ для вопроса
        s_question = data[s_question_key]           # вопрос из FSMContext хранилища

        s_answer_key = 's_answer' + str(i)          # ключ для ответа
        s_answer = data[s_answer_key]               # ответ из FSMContext хранилища

        if s_question == s_answer:
            i_correct += 1

    # предоставляется строка с результатом
    return f'Результат: {i_correct} из {i_size} или {(i_correct / i_size) * 100}%'


def get_questions_from_source(size: int) -> list[tuple[str, list[str], str]]:
    """
    Формирование списка вопросов размером size из источника.
    Формат объекта вопроса: (текст вопроса, [варианты ответов], правильный ответ).

    :param size:
    :return:
    """
    return random.sample(questions_source, size)


def create_questions_dict(v_in_list_questions: list[tuple[str, list[str], str]]) -> Dict[str, Any]:
    """
    Формирование словаря с ключами:
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

        for i_list_answers_index in range(len(v_in_list_questions[i_list_questions_index][1])):
            # нумерация полей s_answer# в StateTestAnswer начинается с 1
            i_k = i_list_answers_index + 1

            s_answer_key = 's_answer' + str(i_list_questions_index * 4 + i_k)
            s_answer_value = v_in_list_questions[i_list_questions_index][1][i_list_answers_index]
            dict_result[s_answer_key] = s_answer_value

    return dict_result


async def save_user_data(v_in_message, v_in_state):
    data = await v_in_state.update_data(
        s_message_id=str(v_in_message.message_id),
        user_id=v_in_message.from_user.id,
        s_username=v_in_message.from_user.username,
        s_first_name=v_in_message.from_user.first_name,
        s_last_name=v_in_message.from_user.last_name,
        s_language_code=v_in_message.from_user.language_code,
        s_is_premium=v_in_message.from_user.is_premium,
        dt_dateupd=time.time()
    )
    print(data)
