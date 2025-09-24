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
        if chat_id == -1001635093935:
            daily_message = params.generate_old_daily_message(chat_id)
        else:
            daily_message = params.generate_daily_message(chat_id)
        await bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                       caption=daily_message, parse_mode='HTML',
                                       reply_markup=keyboard.get_vote_button_keyboard())

    @dp.callback_query(F.data == "user_voted")
    async def handle_vote_callback(callback: CallbackQuery):
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        user_name = callback.from_user.full_name
        user_login = callback.from_user.username
        current_date = datetime.now().strftime("%Y-%m-%d")

        log(f"chat_id ({chat_id}): {user_id} - нажал на кнопку голосования")

        result = db.get_data_from_db(f"SELECT * FROM voters where user_id = {user_id} and vote_date = '{current_date}'")

        # Проверяем, голосовал ли пользователь сегодня
        if len(result) > 0:
            await callback.answer("Ты уже голосовал сегодня! Ждём твой голос завтра!", show_alert=True)
            log(f"chat_id ({chat_id}): {user_id} - уже голосовал")
            return

        # Добавляем пользователя в список голосовавших сегодня
        db.add_voter(user_id, chat_id, user_name, user_login, current_date)

        await callback.answer("Спасибо за твой голос! Приходи голосовать завтра =)", show_alert=True)
        log(f"chat_id ({chat_id}): {user_id} - голос засчитан")

        await update_message(chat_id, params.get_last_message_id(chat_id))
