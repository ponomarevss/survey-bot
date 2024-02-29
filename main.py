import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from admin import API_TOKEN, DB_URL
from handlers import rt
from middlewares import DbSessionMiddleware, CheckSessionMiddleware
from models import Base


async def start():
    engine = create_engine(url=DB_URL)
    Base.metadata.create_all(engine)

    bot = Bot(API_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    # dp.message.middleware.register(AntispamMiddleware(v_in_i_cooldown=3))
    dp.update.middleware.register(DbSessionMiddleware(session=Session(engine)))
    dp.callback_query.middleware.register(CheckSessionMiddleware())

    dp.include_router(router=rt)

    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
