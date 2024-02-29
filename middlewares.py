import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy.orm import Session


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        with self.session as session:
            data["session"] = session
            return await handler(event, data)


class AntispamMiddleware(BaseMiddleware):
    def __init__(self, v_in_i_cooldown: int) -> None:
        self.f_timestamp = 0.0
        self.i_cooldown = v_in_i_cooldown

    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        f_timestamp = time.time()
        if f_timestamp - self.f_timestamp > self.i_cooldown:
            self.f_timestamp = f_timestamp
            return await handler(event, data)
        else:
            return


class CheckSessionMiddleware(BaseMiddleware):
    async def __call__(
            self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        event_data_id = event.data.split('_')[2]
        dict_data = await data['state'].get_data()
        s_message_id = dict_data['s_message_id']
        if event_data_id == s_message_id:
            return await handler(event, data)
        else:
            return
