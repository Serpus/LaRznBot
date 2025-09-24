from bkVote import callbacks, bk
from novice import novice_listner

from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import ErrorEvent
from dotenv import load_dotenv
from bot_logger import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import os

load_dotenv()
bot = Bot(token=os.getenv("API_KEY"))
router = Router()
dp = Dispatcher()
dp.include_router(router)

callbacks.register(dp, bot)
bk.register(dp, bot)
novice_listner.register(router)


# @dp.message(Command("test"))
async def test(message: types.Message):
    await message.answer("Тестовое сообщение")
    # await bot.send_message(chat_id=chat_id_slujebka, text="Тестовое сообщение")


@dp.error()
async def handle_errors(error: ErrorEvent):
    log(f"Ошибка: {error}")


async def on_startup(scheduler: AsyncIOScheduler):
    # Планируем первую задачу
    await bk.schedule_daily_job(scheduler, bot)

    # Перепланирование на завтра (чтобы каждый день было новое случайное время)
    async def reschedule():
        while True:
            delay = bk.get_next_10am(scheduler)
            await bot.send_message(chat_id=649062985,
                                   text=f"Перепланирование будет в 10:00. Ожидание: {delay:.0f} секунд...")
            log(f"Перепланирование будет в 10:00. Ожидание: {delay:.0f} секунд...")
            await asyncio.sleep(delay)
            await bk.schedule_daily_job(scheduler, bot)

    # Запускаем фоновую задачу для перепланирования
    asyncio.create_task(reschedule())


async def main():
    # Запускаем планировщик
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")  # Укажите нужный часовой пояс
    scheduler.start()

    # При старте сразу планируем задачу
    # await on_startup(scheduler)

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
