import asyncio
import logging
import sys

from aiogram import F, Bot, Dispatcher
from aiogram.filters import CommandStart
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from admin import API_TOKEN, DB_URL
from handlers import (
    command_start_message_handler,
    unknown_message_handler,
    tech_start_callback_handler,
    tech_ans_callback_handler, first_name_message_handler, last_name_message_handler, phone_input_callback_handler,
    phone_backspace_callback_handler, survey1_message_handler, survey2_message_handler, survey3_message_handler,
    survey4_message_handler, survey5_message_handler, survey6_message_handler, survey7_message_handler,
    psycho_init_callback_handler, psycho_ans_callback_handler, psycho_start_callback_handler
)
from middlewares import DbSessionMiddleware, CheckSessionMiddleware
from models import Base
from states import Form


async def start():
    engine = create_engine(url=DB_URL)
    Base.metadata.create_all(engine)

    bot = Bot(API_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    # dp.message.middleware.register(AntispamMiddleware(v_in_i_cooldown=3))
    dp.update.middleware.register(DbSessionMiddleware(session=Session(engine)))
    dp.callback_query.middleware.register(CheckSessionMiddleware())

    dp.message.register(command_start_message_handler, CommandStart())
    dp.message.register(first_name_message_handler, F.text, Form.s_user_first_name)
    dp.message.register(last_name_message_handler, F.text, Form.s_user_last_name)
    dp.message.register(survey1_message_handler, F.text, Form.s_survey1)
    dp.message.register(survey2_message_handler, F.text, Form.s_survey2)
    dp.message.register(survey3_message_handler, F.text, Form.s_survey3)
    dp.message.register(survey4_message_handler, F.text, Form.s_survey4)
    dp.message.register(survey5_message_handler, F.text, Form.s_survey5)
    dp.message.register(survey6_message_handler, F.text, Form.s_survey6)
    dp.message.register(survey7_message_handler, F.text, Form.s_survey7)
    dp.message.register(unknown_message_handler)

    dp.callback_query.register(phone_input_callback_handler, Form.s_user_phone_num, F.data.startswith("phone"))
    dp.callback_query.register(phone_backspace_callback_handler, Form.s_user_phone_num, F.data.startswith("backspace"))
    dp.callback_query.register(psycho_init_callback_handler, Form.s_user_phone_num, F.data.startswith("confirm"))
    dp.callback_query.register(
        psycho_start_callback_handler, Form.list_psycho_answers, F.data.startswith("start_survey")
    )
    dp.callback_query.register(psycho_ans_callback_handler, Form.list_psycho_answers, F.data.startswith("reply"))
    # dp.callback_query.register(tech_init_callback_handler, Form.list_tech_answers, F.data.startswith("reply"))
    dp.callback_query.register(tech_start_callback_handler, Form.list_tech_answers, F.data.startswith("start_survey"))
    dp.callback_query.register(tech_ans_callback_handler, Form.list_tech_answers, F.data.startswith("ans"))

    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
