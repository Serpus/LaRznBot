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


@dp.message(Command("stats"))
async def count_voters_per_day(message: types.Message):
    """
    Читает файл voters.json и выводит статистику.
    - Без аргументов: общее количество голосов за всё время (без детализации по дням).
    - С аргументом YYYY-MM: детальная статистика по дням указанного месяца + итог.
    Пример: /stats 2025-03
    """
    if message.chat.id != 649062985:
        return
    filename = "resources/voters.json"

    # Извлекаем аргумент (месяц)
    args = message.text.strip().split()
    target_month = args[1] if len(args) > 1 else None

    # Проверка формата месяца
    if target_month and not (len(target_month) == 7 and target_month[4] == '-'):
        await message.answer(
            "❌ Неверный формат месяца. Используйте: <code>YYYY-MM</code>, например <code>2025-03</code>.",
            parse_mode="HTML")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        log(f"Ошибка: файл '{filename}' не найден.")
        await message.answer(f"❌ Файл '{filename}' не найден.")
        return
    except json.JSONDecodeError as e:
        log(f"Ошибка при чтении JSON: {e}")
        await message.answer("❌ Ошибка чтения данных. Файл повреждён.")
        return

    total_count_all = 0
    days_processed = 0
    sent_any_message = False

    # Сортируем даты по хронологии
    sorted_dates = sorted(data.keys())

    for date in sorted_dates:
        # Проверяем формат даты: ожидается YYYY-MM-DD
        if len(date) != 10 or date[4] != '-' or date[7] != '-':
            continue  # пропускаем некорректные даты

        year_month = date[:7]  # YYYY-MM

        # Фильтрация по месяцу, если задан
        if target_month and year_month != target_month:
            continue

        ids = data[date]
        if isinstance(ids, list):
            unique_ids = set(ids)
            count = len(unique_ids)
            total_count_all += count
            days_processed += 1

            # Отправляем информацию по дням ТОЛЬКО если указан месяц
            if target_month:
                stat_text = f"<b>{date}</b>: {count} человек"
                await message.answer(stat_text, parse_mode="HTML")
                sent_any_message = True
        else:
            log(f"{date}: данные повреждены (не список)")

    # Вывод итоговой статистики
    if target_month:
        if days_processed == 0:
            await message.answer(f"📅 За месяц <b>{target_month}</b> нет данных о голосованиях.", parse_mode="HTML")
        else:
            summary = (
                f"\n📊 <b>Итого за месяц {target_month}:</b>\n"
                f"• Дней с голосами: {days_processed}\n"
                f"• Всего голосов: {total_count_all}"
            )
            await message.answer(summary, parse_mode="HTML")
    else:
        # Если месяц не указан — просто общий итог
        if total_count_all == 0:
            await message.answer("📂 Нет данных о голосованиях за всё время.")
        else:
            summary = (
                f"📊 <b>Общая статистика за всё время:</b>\n"
                f"• Дней с голосами: {days_processed}\n"
                f"• Всего голосов: {total_count_all}"
            )
            await message.answer(summary, parse_mode="HTML")


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
