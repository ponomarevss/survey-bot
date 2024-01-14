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
    init_state_message_handler, unknown_message_handler,
    incorrect_button_usage_callback_handler,
    start_survey_callback_handler,
    ans_callback_handler
)
from states import Form


class AntispamMiddleware(BaseMiddleware):
    """
    Задача AntispamMiddleware ловить частые текстовые сообщения во всех возможных случаях
    """

    def __init__(self, cooldown: int) -> None:
        self.timestamp = time.time()
        self.cooldown = cooldown

    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # сохранение значения времени получения апдейта
        timestamp = time.time()

        # апдейт дойдет до хендлеров если будут выполнены условия:
        #   он пришел позже self.cooldown
        #           или
        #   если после команды '/start', когда активное состояние FSM соответствует 'Form:user_name',
        #   сразу следует текстовое сообщение отличное от '/start'
        if ((not self.iscommand_start(data)) & self.isname_state(data)) | (timestamp - self.timestamp > self.cooldown):
            self.timestamp = timestamp  # обновление значения времени последнего апдейта
            return await handler(event, data)
        else:
            return

    @staticmethod
    def iscommand_start(data: Dict[str, Any]) -> bool:
        # проверка текста сообщения на соответствие '/start'
        return data['event_update'].message.text == '/start'

    @staticmethod
    def isname_state(data: Dict[str, Any]) -> bool:
        # проверка активного состояния FSM на соответствие 'Form:user_name'
        return data['raw_state'] == 'Form:user_name'


async def start():
    # сохранение экземпляров Bot и Dispatcher
    bot = Bot(API_TOKEN)
    dp = Dispatcher()

    # регистрация хендлеров для Message
    dp.message.register(command_start_message_handler, CommandStart())
    dp.message.register(init_state_message_handler, Form.s_user_name)
    dp.message.register(unknown_message_handler)

    # регистрация хендлеров для CallbackQuery
    dp.callback_query.register(start_survey_callback_handler, Form.list_answers, F.data.startswith("start_survey"))
    dp.callback_query.register(ans_callback_handler, Form.list_answers, F.data.startswith("ans"))
    dp.callback_query.register(incorrect_button_usage_callback_handler)

    # регистрация Middleware
    # dp.message.middleware.register(AntispamMiddleware(cooldown=5))

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
