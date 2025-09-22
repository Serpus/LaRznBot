import json
import os
from datetime import datetime
import params
import db

from aiogram import Dispatcher, F, Bot
from aiogram.types import CallbackQuery

import keyboard
from bot_logger import log


def register(dp: Dispatcher, bot: Bot):
    async def update_message(chat_id, message_id: int):
        await bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                       caption=params.generate_daily_message(chat_id), parse_mode='HTML',
                                       reply_markup=keyboard.get_vote_button_keyboard())

    @dp.callback_query(F.data == "user_voted")
    async def handle_vote_callback(callback: CallbackQuery):
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        log(f"chat_id ({chat_id}): {user_id} - нажал на кнопку голосования")
        current_date = datetime.now().strftime("%Y-%m-%d")

        result = db.get_data_from_db(f"SELECT * FROM voters where user_id = 649062985 and vote_date = '2025-09-19'")

        # Проверяем, голосовал ли пользователь сегодня
        if len(result) > 0:
            await callback.answer("Ты уже голосовал сегодня! Ждём твой голос завтра!", show_alert=True)
            log(f"{user_id} - уже голосовал")
            return

        # Добавляем пользователя в список голосовавших сегодня
        db.add_voter(user_id, chat_id, "", "", current_date)

        await callback.answer("Спасибо за твой голос! Приходи голосовать завтра =)", show_alert=True)
        log(f"{user_id} - голос засчитан")

        await update_message(chat_id, params.get_last_message_id(chat_id))


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
