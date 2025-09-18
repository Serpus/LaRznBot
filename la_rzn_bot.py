import random
from datetime import datetime, timedelta, time
from email.policy import default

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.command import CommandPatternType
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from dotenv import load_dotenv
from bot_logger import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import os

load_dotenv()
bot = Bot(token=os.getenv("API_KEY"))
dp = Dispatcher()
chat_id_slujebka = -1003043852228
vote_link = "https://burgerkingapp.onelink.me/220f/g4k9umfa"
short_vote_link = "https://clck.ru/3PHUak"
# -1001635093935 - реальный чат ЛА
la_chat_id = -1002911410297
# 7684 - реальная тема с БК голосованием
bk_thread_id = 4
reply_message_id = 37
message_text = f"""Для вашего удобства взяли с сайта БК QR-код и ссылку, по которой можно перейти и сразу попасть на страницу с голосованием*
{short_vote_link}

<i>*Приложение должно быть установлено</i>"""


# Проверка, является ли пользователь администратором
async def is_admin(chat_id, user_id):
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))


# @dp.message(Command("test"))
async def test(message: types.Message):
    await message.answer("Тестовое сообщение")
    # await bot.send_message(chat_id=chat_id_slujebka, text="Тестовое сообщение")


@dp.message(Command("answer"))
async def answer(message: types.Message):
    await bot.send_message(chat_id=la_chat_id, message_thread_id=bk_thread_id,
                           reply_to_message_id=reply_message_id, text="test")


@dp.message(Command("message"))
async def send_message(message: types.Message):
    sent_message = await bot.send_photo(chat_id=la_chat_id, message_thread_id=bk_thread_id,
                                        photo=types.FSInputFile("resources\\qr.png"),
                                        caption=message_text, parse_mode="HTML")
    log(f"ID отправленного сообщения: {sent_message.message_id}")


@dp.message()
async def echo(message: types.Message):
    log(f"Получено сообщение с id {message.message_id}, "
        f"группа {message.chat.id}, "
        f"тема {message.message_thread_id} (), "
        f"от {message.from_user.username}")


@dp.error()
async def handle_errors(event, exception):
    log(f"Ошибка: {exception}")


async def send_daily_message():
    try:
        # await bot.send_message(chat_id=la_chat_id, message_thread_id=bk_thread_id,
        #                        reply_to_message_id=reply_message_id, text=message_text)
        log("Сообщение отправлено!")
    except Exception as e:
        log(f"Ошибка при отправке сообщения: {e}")


def get_random_time_between_11_and_12():
    """Возвращает случайное время между 11:00 и 11:59"""
    minute = random.randint(0, 29)
    second = random.randint(0, 59)
    return time(11, minute, second)


async def schedule_daily_job(scheduler: AsyncIOScheduler):
    # Сначала удаляем старую задачу, если она была
    scheduler.remove_all_jobs()

    # Получаем случайное время
    random_time = get_random_time_between_11_and_12()

    # Планируем задачу на это время каждый день
    scheduler.add_job(
        send_daily_message,
        trigger=CronTrigger(
            hour=random_time.hour,
            minute=random_time.minute,
            second=random_time.second,
            day="*"
        ),
        id="daily_message",
        replace_existing=True,
        name="Ежедневное сообщение в случайное время с 11 до 12"
    )

    text = f"Отправка сообщения запланирована на {random_time.strftime('%H:%M:%S')}"
    await bot.send_message(chat_id=649062985, text=text)
    log(text)


def get_next_10am(scheduler: AsyncIOScheduler) -> float:
    now = datetime.now(scheduler.timezone)
    next_10am = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if now.time() < time(10, 0):
        # Если сейчас ещё до 10:00, то ждём сегодняшних 10:00
        next_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
    delay = (next_10am - now).total_seconds()
    return max(delay, 0)


async def on_startup(scheduler: AsyncIOScheduler):
    # Планируем первую задачу
    await schedule_daily_job(scheduler)

    # Перепланирование на завтра (чтобы каждый день было новое случайное время)
    async def reschedule():
        while True:
            delay = get_next_10am(scheduler)
            # await bot.send_message(chat_id=649062985,
            #                        text=f"Перепланирование будет в 10:00. Ожидание: {delay:.0f} секунд...")
            log(f"Перепланирование будет в 10:00. Ожидание: {delay:.0f} секунд...")
            await asyncio.sleep(delay)
            await schedule_daily_job(scheduler)

    # Запускаем фоновую задачу для перепланирования
    asyncio.create_task(reschedule())


async def main():
    # Запускаем планировщик
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")  # Укажите нужный часовой пояс
    scheduler.start()

    # При старте сразу планируем задачу
    await on_startup(scheduler)

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
