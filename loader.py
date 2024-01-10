import os

from aiogram import Dispatcher, Bot

token = os.getenv("BOT_TOKEN")
dp = Dispatcher()
bot = Bot(token)
