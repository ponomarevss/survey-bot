import asyncio
import logging
import sys
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import F, Bot, Dispatcher, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import TelegramObject, Message

from admin import API_TOKEN
from callback_query import (
    command_start_message_handler,
    init_quiz_callback_handler, unknown_message_handler,
    incorrect_button_usage_callback_handler,
    start_survey_callback_handler,
    ans_callback_handler, first_name_message_handler, last_name_message_handler, phone_input_callback_handler,
    phone_backspace_callback_handler
)
from states import Form


class AntispamMiddleware(BaseMiddleware):
    """
    Задача AntispamMiddleware ловить частые текстовые сообщения
    """

    def __init__(self, v_in_i_cooldown: int) -> None:
        self.f_timestamp = 0.0
        self.i_cooldown = v_in_i_cooldown

    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # сохранение значения времени получения апдейта
        f_timestamp = time.time()

        # если разница временных отметок более i_cooldown
        if f_timestamp - self.f_timestamp > self.i_cooldown:
            self.f_timestamp = f_timestamp      # обновление значения времени последнего апдейта
            return await handler(event, data)   # апдейт идет к хендлерам
        else:
            return                              # иначе дроп апдейта


# сохранение экземпляров Bot и Dispatcher
bot = Bot(API_TOKEN, parse_mode="HTML")
dp = Dispatcher()


async def start():

    # регистрация хендлеров для Message
    dp.message.register(command_start_message_handler, CommandStart())
    dp.message.register(first_name_message_handler, F.text, Form.s_user_first_name)
    dp.message.register(last_name_message_handler, F.text, Form.s_user_last_name)
    dp.message.register(unknown_message_handler)

    # регистрация хендлеров для CallbackQuery
    dp.callback_query.register(phone_input_callback_handler, Form.s_user_phone_num, F.data.startswith("phone"))
    dp.callback_query.register(phone_backspace_callback_handler, Form.s_user_phone_num, F.data.startswith("backspace"))
    dp.callback_query.register(init_quiz_callback_handler, Form.s_user_phone_num, F.data.startswith("confirm"))
    dp.callback_query.register(start_survey_callback_handler, Form.list_answers, F.data.startswith("start_survey"))
    dp.callback_query.register(ans_callback_handler, Form.list_answers, F.data.startswith("ans"))
    dp.callback_query.register(incorrect_button_usage_callback_handler)

    # регистрация Middleware
    dp.message.middleware.register(AntispamMiddleware(v_in_i_cooldown=3))

    # запуск сессии бота с закрытием при ошибке
    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
