import json
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from dotenv import load_dotenv
from bot_logger import log

import os

load_dotenv()
bot = Bot(token=os.getenv("API_KEY"))
dp = Dispatcher()
chat_id_slujebka=-1003043852228

# Проверка, является ли пользователь администратором
async def is_admin(chat_id, user_id):
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))

# @dp.message(Command("test"))
async def echo(message: types.Message):
    await bot.send_message(chat_id=chat_id_slujebka, text="Тестовое сообщение")

@dp.error()
async def handle_errors(event, exception):
    log(f"Ошибка: {exception}")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())