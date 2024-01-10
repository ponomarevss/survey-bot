import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


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
