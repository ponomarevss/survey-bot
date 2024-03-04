import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from aioschedule import Scheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from admin import API_TOKEN, DB_URL, CACHE_URL
from handlers import rt
from middlewares import DbSessionMiddleware, CheckSessionMiddleware, CacheMiddleware
from models import Base
from utils import get_user_id_list


async def start():
    engine = create_engine(url=DB_URL)
    Base.metadata.create_all(engine)

    bot = Bot(API_TOKEN, parse_mode="HTML")
    storage = RedisStorage.from_url(url=CACHE_URL, connection_kwargs={"decode_responses": True})

    dp = Dispatcher(storage=storage)

    # dp.message.middleware.register(AntispamMiddleware(v_in_i_cooldown=3))
    dp.update.middleware.register(CacheMiddleware(redis_storage=storage))
    dp.update.middleware.register(DbSessionMiddleware(session=Session(engine)))
    dp.callback_query.middleware.register(CheckSessionMiddleware())

    dp.include_router(router=rt)

    # keys = await storage.redis.keys()
    # for k in keys:
    #     if '324901643' in k:
    #         await storage.redis.delete(k)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_user_id_list, trigger='interval', seconds=5, kwargs={'storage': storage})
    scheduler.start()

    try:
        await dp.start_polling(bot)
    except Exception as _ex:
        print(f"There is an exception - {_ex}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
