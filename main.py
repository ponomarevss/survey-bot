import asyncio
import logging
import sys

from aiogram import F
from aiogram.filters import CommandStart

from handlers.form_handlers import process_command_start, process_init_state, unknown_message, incorrect_button_usage, \
    process_start_survey_callback, process_ans_callback
from loader import dp, bot
from middlewares.form_middlewares import AntispamMiddleware
from states import Form


async def start():
    dp.message.register(process_command_start, CommandStart())
    dp.message.register(process_init_state, Form.user_name)
    dp.callback_query.register(process_start_survey_callback, Form.answers, F.data.startswith("start_survey"))
    dp.callback_query.register(process_ans_callback, Form.answers, F.data.startswith("ans"))

    dp.message.register(unknown_message)
    dp.callback_query.register(incorrect_button_usage)

    dp.message.middleware.register(AntispamMiddleware())

    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
