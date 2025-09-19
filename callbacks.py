import json
import os
from datetime import datetime
import params

from aiogram import Dispatcher, F, Bot
from aiogram.types import CallbackQuery

import keyboard
from bot_logger import log


def register(dp: Dispatcher, bot: Bot):
    def generate_daily_message():
        with open('resources/vote_count', 'r') as file:
            vote_count = int(file.read().strip())
        return f"""Напоминаем, что <b>голосовать можно каждый день</b>
Сегодня новый день и новая возможность помочь отряду

<u>Самый энергичный по голосованию регион оденется в отрядную форму!</u>

Ссылка для голосования: {params.short_vote_link}
Полная инструкция с видео: {params.bk_instruction_post}

<i>Мы проголосовали: {vote_count} раз(а)</i>

<b>Проголосовал - нажми кнопку (работает раз в день)</b>"""

    async def update_message(message_id: int):
        await bot.edit_message_caption(chat_id=params.la_chat_id, message_id=message_id,
                                       caption=generate_daily_message(), parse_mode='HTML',
                                       reply_markup=keyboard.get_vote_button_keyboard())

    @dp.callback_query(F.data == "user_voted")
    async def handle_vote_callback(callback: CallbackQuery):
        user_id = callback.from_user.id
        log(f"{user_id} - нажал на кнопку голосования")
        current_date = datetime.now().strftime("%Y-%m-%d")
        count = 0

        # Путь к файлам
        vote_count_file = "resources/vote_count"
        voters_file = "resources/voters.json"

        # Загружаем данные о голосовавших
        if os.path.exists(voters_file):
            with open(voters_file, "r", encoding="utf-8") as f:
                voters_data = json.load(f)
        else:
            voters_data = {}

        # Проверяем, голосовал ли пользователь сегодня
        if current_date in voters_data:
            if str(user_id) in voters_data[current_date]:
                await callback.answer("Ты уже голосовал сегодня! Ждём твой голос завтра!", show_alert=True)
                log(f"{user_id} - уже голосовал")
                return
        else:
            voters_data[current_date] = []

        # Добавляем пользователя в список голосовавших сегодня
        voters_data[current_date].append(str(user_id))

        # Сохраняем обновленные данные
        with open(voters_file, "w", encoding="utf-8") as f:
            json.dump(voters_data, f, ensure_ascii=False, indent=2)

        # Увеличиваем счетчик голосов
        try:
            with open(vote_count_file, "r") as f:
                count = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            pass

        count += 1

        with open(vote_count_file, "w") as f:
            f.write(str(count))

        await callback.answer("Спасибо за твой голос! Приходи голосовать завтра =)", show_alert=True)
        log(f"{user_id} - голос засчитан")

        await update_message(params.get_last_message_id())


def cleanup_old_voter_data(days_to_keep=7):
    """Удаляет данные о голосовавших старше указанного количества дней"""
    voters_file = "resources/voters.json"

    if not os.path.exists(voters_file):
        return

    with open(voters_file, "r", encoding="utf-8") as f:
        voters_data = json.load(f)

    cutoff_date = datetime.now().date()
    keys_to_delete = []

    for date_str in voters_data.keys():
        try:
            vote_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if (cutoff_date - vote_date).days > days_to_keep:
                keys_to_delete.append(date_str)
        except ValueError:
            keys_to_delete.append(date_str)  # Удаляем некорректные даты

    for key in keys_to_delete:
        del voters_data[key]

    with open(voters_file, "w", encoding="utf-8") as f:
        json.dump(voters_data, f, ensure_ascii=False, indent=2)
