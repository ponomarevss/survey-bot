import asyncio
import logging
import os
import sys
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import F, Bot, Dispatcher, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import TelegramObject, Message

from callback_query import command_start_message_handler, init_state_message_handler, unknown_message_handler, \
    incorrect_button_usage_callback_handler, \
    start_survey_callback_handler, ans_callback_handler
from states import Form


class AntispamMiddleware(BaseMiddleware):
    def __init__(self, cooldown: int) -> None:
        self.timestamp = time.time()
        self.cooldown = cooldown

    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        timestamp = time.time()
        # сложное условие: сообщение попадет в хендлер если стейт Form:user_name и при этом текст не "/start"
        # или если не прошел кулдаун
        if (((data['event_update'].message.text != '/start') & (data['raw_state'] == 'Form:user_name'))
                | (timestamp - self.timestamp > self.cooldown)):
            self.timestamp = timestamp
            return await handler(event, data)
        else:
            return


async def start():
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    dp.message.register(command_start_message_handler, CommandStart())
    dp.message.register(init_state_message_handler, Form.user_name)
    dp.message.register(unknown_message_handler)

    dp.callback_query.register(start_survey_callback_handler, Form.answers, F.data.startswith("start_survey"))
    dp.callback_query.register(ans_callback_handler, Form.answers, F.data.startswith("ans"))
    dp.callback_query.register(incorrect_button_usage_callback_handler)

    dp.message.middleware.register(AntispamMiddleware(cooldown=5))

    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
