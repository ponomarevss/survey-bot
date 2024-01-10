import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class AntispamMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.timestamp = time.time()

    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        timestamp = time.time()
        if timestamp - self.timestamp > 3:
            self.timestamp = timestamp
            return await handler(event, data)
        else:
            return
