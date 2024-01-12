import random
import uuid
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
    await state.clear()                                     # сброс предыдущего состояния FSM
    await state.update_data(session_id=str(uuid.uuid4()))   # установка нового session_id
    await state.set_state(Form.user_name)                   # установка активного состояния FSM

    # обращение к респонденту, запрос имени
    text = (f"Добро пожаловать! Это бот для теста знаний.\n"
            f"Как я могу к вам обращаться? (Введите свое имя)")
    await message.answer(text=text)


async def init_state_message_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка текстового сообщения после установки 'Form:user_name' в качестве активного состояния FSM.

    :param message:
    :param state:
    :return:
    """
    size = 10  # количество вопросов в тесте

    # установка и получение данных FSM
    data = await state.update_data(
        user_name=message.text,                 # имя респондента
        current_index=0,                        # исходный индекс для обращения к спискам вопросов и ответов
        questions=get_questions(size),          # список вопросов из источника
        answers=[None for _ in range(size)]     # пустой лист ответов
    )
    await state.set_state(Form.answers)         # установка активного состояния FSM

    # обращение к респонденту, получение кнопки запуска теста
    text = (f"Уважаемый {data['user_name']}, давайте начнем наш тест.\n"
            f"Нажмите кнопку 'Начать тест', когда будете готовы.")
    await message.answer(text=text, reply_markup=get_start_survey_ikb(data))


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
    data = await state.get_data()       # получение данных из FSM

    # проверка эквивалентности session_id полученному из коллбэка
    if data['session_id'] == callback.data.split('_')[2]:

        # вывод вопроса и клавиатуры с вариантами ответа
        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        await state.update_data(current_index=data['current_index'] + 1)   # инкремент текущего индекса в FSM
    else:

        # выполнение действий, связанных с некорректным использованием кнопок
        await incorrect_button_usage_callback_handler(callback)


async def ans_callback_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка коллбэка ответов на вопросы. Задача:
    - проверить коллбэк на соответствие текущему session_id;
    - в случае провала, выполнить действия, связанные с некорректным использованием кнопок;
    - в случае успеха, выполнить проверку, является ли вопрос последним:
        - если вопрос не последний, отобразить ответ на предыдущий вопрос,
            вывести следующий вопрос и клавиатуру с вариантами ответов;
        - если вопрос последний, отобразить ответ на предыдущий вопрос, отобразить результаты теста.

    :param callback:
    :param state:
    :return:
    """
    data = await state.get_data()       # получение данных из FSM

    # проверка эквивалентности session_id полученному из коллбэка
    if data['session_id'] == callback.data.split('_')[2]:

        # обновление данных FSM на основе данных коллбэка
        await state.update_data(answers=compose_updated_answers(callback.data, data))

        # в зависимости от того, последний вопрос или нет:
        #   вывод ответа на предыдущий вопрос,
        #   текущего вопроса,
        #   результата теста
        await callback.message.edit_text(compose_text(data), reply_markup=get_answers_ikb(data))

        current_index = data['current_index']                                   # получение текущего индекса

        # проверка текущего индекса:
        #   если индекс за пределами листа вопросов, активное сбросить состояние FSM, если нет, выполнить инкремент
        if current_index in range(0, len(data['questions'])):
            await state.update_data(current_index=data['current_index'] + 1)    # инкремент текущего индекса в FSM
        else:
            await state.set_state(None)                                         # установка активного состояния FSM

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


def get_start_survey_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры для начала теста. Формирование коллбэка с session_id.

    :param data:
    :return:
    """
    session_id = data['session_id']                   # получение session_id из FSM
    callback_data = f'start_survey_{session_id}'   # формирование коллбэка с session_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать тест", callback_data=callback_data)]
        ]
    )


def get_answers_ikb(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Предоставление клавиатуры с вариантами ответа, либо None, если текущий индекс за пределами листа вопросов.
    Формирование коллбэков на основе префикса "ans", хэш значения варианта ответа и session_id.

    :param data:
    :return:
    """
    buttons = list()
    ind = data['current_index']         # текущий индекс
    questions = data['questions']       # список вопросов
    session_id = data['session_id']           # session_id
    ikb = None

    # проверка индекса на вхождение в лист вопросов
    if ind in range(len(questions)):
        question = questions[ind]       # объект вопрос: (текст вопроса, [варианты ответов], правильный ответ)
        answers = question[1]           # варианты ответов

        # формирование списка кнопок с вариантами ответов
        for element in answers:
            callback_data = f"ans_{hash(element)}_{session_id}"    # коллбэк с хэш варианта ответа и session_id
            buttons.append(InlineKeyboardButton(text=element, callback_data=callback_data))

        # формирование клавиатуры 2 на 2
        ikb = InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])
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
    questions = data['questions']           # список вопрос: [(текст вопроса, [варианты ответов], правильный ответ)]
    current_index = data['current_index']   # текущий индекс
    answers = data['answers']               # список правильных ответов
    name = data['user_name']                # user_name
    text = f'Тестирование кандидата {name}:\n\n'          # часть текста с обращением

    # цикл с формированием текста для элементов списка вопросов и ответов от 0 до текущего
    for i in range(current_index + 1):
        prev_index = i - 1                                  # индекс ответа на предыдущий вопрос

        # проверка наличия предыдущего вопроса
        if prev_index in range(len(questions)):
            text += f'Ответ: {answers[prev_index]}\n\n'     # добавление ответа на предыдущий вопрос
        question_num = i + 1                                # номер вопроса для отображения

        # проверка наличия вопроса для текущего индекса
        if i in range(len(questions)):
            text += f'{question_num}. {questions[i][0]}\n'  # добавление текущего вопроса
        else:
            text += calculate_result(data)                  # вывод результата теста
    return text


def compose_updated_answers(callback_str: str, data: Dict[str, Any]) -> List[str]:
    """
    Формирование обновленного листа ответов на основе данных FSM и полученного коллбэка.

    :param callback_str:
    :param data:
    :return:
    """
    answers = data['answers']                   # список ответов из FSM
    prev_ind = data['current_index'] - 1        # предыдущий индекс
    options = data['questions'][prev_ind][1]    # ответы из (текст вопроса, [варианты ответов], правильный ответ)

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
    callback_hash = int(callback_str.split('_')[1])     # хэш ответа из коллбэка

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
    questions = data['questions']           # список вопрос: [(текст вопроса, [варианты ответов], правильный ответ)]
    answers = data['answers']               # список ответов
    correct = 0                             # счетчик правильных ответов
    size = len(answers)                     # количество вопросов

    # поиск совпадений ответов с правильным из объекта (текст вопроса, [варианты ответов], правильный ответ)
    # с соответствующим инкрементом счетчика правильных ответов
    for i in range(size):
        if questions[i][2] == answers[i]:
            correct += 1

    # предоставляется строка с результатом
    return f'Результат: {correct} из {size} или {(correct / size) * 100}%'


def get_questions(size: int) -> list[tuple[str, list[str], str]]:
    """
    Формирование списка вопросов размером size из источника.
    Формат объекта вопроса: (текст вопроса, [варианты ответов], правильный ответ).

    :param size:
    :return:
    """
    return random.sample(questions_source, size)
