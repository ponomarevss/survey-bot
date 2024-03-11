import random
from datetime import datetime
from typing import Dict, Any, List

from aiogram.fsm.storage.redis import RedisStorage

from models import User, Log
from source import OPTIONS_NUM, tech_questions_source, psycho_questions_source


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


async def save_user_data(v_in_message, v_in_state, v_in_session):
    await save_t_user(v_in_message, v_in_session)
    await save_user_to_cache(v_in_message, v_in_state)


"""сохранять в кеш вопросики, ответики, варианты ответов, правильный ответ, обновлять dt_dateupd
"""
# TODO: это сохранение в кэш при запуске сессии по команде старт
async def save_user_to_cache(v_in_message, v_in_storage: RedisStorage):
    prefix = str(v_in_message.from_user.id)
    redis = v_in_storage.redis
    await redis.set(prefix + 's_message_id', v_in_message.message_id)
    await redis.set(prefix + 'user_id', v_in_message.from_user.id)
    await redis.set(prefix + 'dt_dateupd', str(datetime.now()))


async def get_user_id_list(storage: RedisStorage) -> List[str]:
    list_result: List[str] = list()
    keys = await storage.redis.keys()
    for k in keys:
        if 'user_id' in k:
            list_result.append(await storage.redis.get(k))
    return list_result


async def save_t_user(v_in_message, v_in_session):
    incoming_user = User(
        user_id=v_in_message.from_user.id,
        s_username=v_in_message.from_user.username,
        s_firstname=v_in_message.from_user.first_name,
        s_lastname=v_in_message.from_user.last_name,
        s_language_code=v_in_message.from_user.language_code,
        s_is_premium=v_in_message.from_user.is_premium,
        dt_dateupd=datetime.now()
    )
    v_in_session.merge(incoming_user)
    v_in_session.commit()


async def save_message_to_t_log(v_in_message, s_question, v_in_session):
    incoming_log = Log(
        user_id=v_in_message.from_user.id,
        s_username=v_in_message.from_user.username,
        s_firstname=v_in_message.from_user.first_name,
        s_lastname=v_in_message.from_user.last_name,
        s_language_code=v_in_message.from_user.language_code,
        s_is_premium=v_in_message.from_user.is_premium,
        s_question=s_question,
        s_answer=v_in_message.text,
        dt_dateupd=datetime.now()
    )
    v_in_session.merge(incoming_log)
    v_in_session.commit()


async def save_callback_to_t_log(v_in_callback, s_question, s_answer, v_in_session):
    incoming_log = Log(
        user_id=v_in_callback.message.from_user.id,
        s_username=v_in_callback.message.from_user.username,
        s_firstname=v_in_callback.message.from_user.first_name,
        s_lastname=v_in_callback.message.from_user.last_name,
        s_language_code=v_in_callback.message.from_user.language_code,
        s_is_premium=v_in_callback.message.from_user.is_premium,
        s_question=s_question,
        s_answer=s_answer,
        dt_dateupd=datetime.now()
    )
    v_in_session.merge(incoming_log)
    v_in_session.commit()
