from typing import Dict, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from source import OPTIONS_NUM


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
