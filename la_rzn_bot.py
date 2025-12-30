import json
import random

from aiogram.filters import Command

import callbacks
import keyboard
from datetime import datetime, timedelta, time
import params
import db

from aiogram import Bot, Dispatcher, types
from aiogram.types import ErrorEvent
from dotenv import load_dotenv
from bot_logger import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import os

load_dotenv()
bot = Bot(token=os.getenv("API_KEY"))
dp = Dispatcher()

message_text = f"""Для вашего удобства взяли с сайта БК QR-код и ссылку, по которой можно перейти и сразу попасть на страницу с голосованием*
{params.short_vote_link}
По вопросам: @Serpus1

<i>*Приложение должно быть установлено</i>"""

callbacks.register(dp, bot)


# @dp.message(Command("test"))
async def test(message: types.Message):
    await message.answer("Тестовое сообщение")
    # await bot.send_message(chat_id=chat_id_slujebka, text="Тестовое сообщение")


# @dp.message(Command("message"))
async def send_message(message: types.Message):
    sent_message = await bot.send_photo(chat_id=params.la_chat_id, message_thread_id=params.bk_thread_id,
                                        photo=types.FSInputFile("resources/qr.png"),
                                        caption=message_text, parse_mode="HTML")
    log(f"ID отправленного сообщения: {sent_message.message_id}")
    params.set_reply_message_id(sent_message.message_id)
    params.set_last_message_id(0)


@dp.message(Command("daily"))
async def daily(message: types.Message):
    if message.chat.id == 649062985:
        await send_daily_message()


@dp.message(Command("all_stats"))
async def count_voters_per_day(message: types.Message):
    if message.chat.id not in (649062985, -2869358118):
        return
    # Получаем аргументы команды
    command_parts = message.text.split()
    date_filter = command_parts[1] if len(command_parts) > 1 else None

    # Формируем условие WHERE
    if date_filter:
        # Проверяем формат YYYY-MM
        try:
            year, month = map(int, date_filter.split('-'))
            # Формируем диапазон дат для месяца
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-31"
            where_clause = f"WHERE vote_date >= ? AND vote_date <= ?"
            parameters = [start_date, end_date]
        except ValueError:
            await message.answer("Неверный формат даты. Используйте YYYY-MM.")
            return
    else:
        where_clause = ""
        parameters = []

    # Запрос: считаем количество голосов по chat_id
    query = f"""
    SELECT 
        v.chat_id,
        r.region_name,
        COUNT(*) as vote_count
    FROM voters v
    JOIN region_chats r on r.chat_id = v.chat_id
    {where_clause}
    GROUP BY v.chat_id
    ORDER BY vote_count DESC;
    """

    try:
        results = db.get_data_from_db_params(query, parameters)

        # Формируем ответ
        if not results:
            await message.answer("Нет данных за выбранный период.")
        else:
            response_lines = []
            for row in results:
                name = row.get("region_name")
                count = row.get("vote_count")
                if date_filter:
                    response_lines.append(f"💬 {name} ({date_filter}): {count} голоса(-ов)")
                else:
                    response_lines.append(f"💬 {name}: {count} голоса(-ов)")

            result_text = "\n".join(response_lines)
            await message.answer(result_text)

    except Exception as e:
        await message.answer("Произошла ошибка при получении статистики.")
        print(f"Ошибка: {e}")


@dp.message(Command("all_stats_day"))
async def all_stats_day(message: types.Message):
    if message.chat.id not in (649062985, -2869358118):
        return
    # Получаем аргументы команды
    command_parts = message.text.split()

    # Проверяем, передан ли аргумент
    if len(command_parts) < 2:
        await message.answer("Пожалуйста, укажите дату в формате YYYY-MM.")
        return

    date_filter = command_parts[1]

    # Проверяем формат YYYY-MM
    try:
        year, month = map(int, date_filter.split('-'))
        if not (1 <= month <= 12):
            raise ValueError("Неверный месяц")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте YYYY-MM.")
        return

    # Определяем первый и последний день месяца
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    # Запрос: считаем количество голосов по дням и чатам
    query = """
    SELECT 
        v.vote_date,
        v.chat_id,
        r.region_name,
        COUNT(*) as vote_count
    FROM voters v
    JOIN region_chats r ON r.chat_id = v.chat_id
    WHERE v.vote_date >= ? AND v.vote_date <= ?
    GROUP BY v.vote_date, v.chat_id
    ORDER BY v.vote_date, vote_count DESC;
    """

    try:
        results = db.get_data_from_db_params(query, [start_date, end_date])

        # Формируем ответ
        if not results:
            await message.answer(f"Нет данных за период {date_filter}.")
        else:
            # Группируем данные по дням
            from collections import defaultdict
            daily_stats = defaultdict(list)

            for row in results:
                vote_date = row.get("vote_date")
                region_name = row.get("region_name")
                vote_count = row.get("vote_count")
                daily_stats[vote_date].append((region_name, vote_count))

            # Формируем текст ответа
            response_lines = [f"📊 Статистика по дням за {date_filter}:"]
            all_votes = 0

            for vote_date in sorted(daily_stats.keys()):
                _votes = 0
                for region_name, vote_count in daily_stats[vote_date]:
                    all_votes += vote_count
                    _votes += vote_count
                    # response_lines.append(f"  💬 {region_name}: {vote_count} голоса(-ов)")
                response_lines.append(f"\n📅 {vote_date}: {_votes} голоса(-ов)")

            result_text = "\n".join(response_lines)
            result_text += f"\n\nВсего голосов за указанный период: {all_votes}"
            await message.answer(result_text)

    except Exception as e:
        await message.answer("Произошла ошибка при получении статистики.")
        print(f"Ошибка: {e}")


@dp.message()
async def echo(message: types.Message):
    log(f"Получено сообщение с id {message.message_id}, "
        f"группа {message.chat.id}, "
        f"тема {message.message_thread_id} (), "
        f"от {message.from_user.username}")


@dp.error()
async def handle_errors(error: ErrorEvent):
    log(f"Ошибка: {error}")


async def send_daily_message():
    for row in db.get_chats():
        chat_id = row.get("chat_id")
        try:
            message_id = params.get_last_message_id(chat_id)
            if message_id is not None:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            log(f"Ошибка при удалении сообщения: {e}")
        try:
            thread_id = db.get_thread_id(chat_id)
            if chat_id == -1001635093935:
                daily_message = params.generate_old_daily_message(chat_id)
            else:
                daily_message = params.generate_daily_message(chat_id)
            reply_message_id = params.get_reply_message_id(chat_id)
            button_keyboard = keyboard.get_vote_button_keyboard()
            sent_message = await bot.send_photo(chat_id=chat_id,
                                                message_thread_id=thread_id,
                                                photo=types.FSInputFile("resources/image.jpg"),
                                                caption=daily_message, parse_mode="HTML",
                                                reply_to_message_id=reply_message_id,
                                                reply_markup=button_keyboard)
            log(f"chat_id {chat_id}: ID отправленного сообщения: {sent_message.message_id}")
            params.set_last_message_id(chat_id, sent_message.message_id)
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
            await bot.send_message(chat_id=649062985,
                                   text=f"Перепланирование будет в 10:00. Ожидание: {delay:.0f} секунд...")
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
