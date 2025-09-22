import db
from bot_logger import log
from db import update_data

chat_id_slujebka = -1003043852228
vote_link = "https://burgerkingapp.onelink.me/220f/g4k9umfa"
short_vote_link = "https://clck.ru/3PHUak"
bk_instruction_post = "https://t.me/lizaalertryazan/7684/7685"

# -1001635093935 - реальный чат ЛА
# -1002911410297 - тестовый чат
# 7684 - реальная тема с БК голосованием
# 4 - тестовая тема


def generate_old_daily_message(chat_id):
    vote_count = get_vote_count(chat_id)
    return f"""Напоминаем, что <b>голосовать можно каждый день</b>
Сегодня новый день и новая возможность помочь отряду

<u>Самый энергичный по голосованию регион оденется в отрядную форму!</u>

Ссылка для голосования: {short_vote_link}
Полная инструкция с видео: {bk_instruction_post}

<i>Мы проголосовали: {vote_count} раз(а)</i>

<b>Проголосовал - нажми кнопку (считаем, сколько людей отдали свой голос от региона)</b>
Что-то не работает? Пиши - @Serpus1
"""


def generate_daily_message(chat_id):
    vote_count = get_vote_count(chat_id)
    return f"""Напоминаем, что <b>голосовать можно каждый день</b>
Сегодня новый день и новая возможность помочь отряду

<u>Самый энергичный по голосованию регион оденется в отрядную форму!</u>

<i>Мы проголосовали: {vote_count} раз(а)</i>

<b>Проголосовал - нажми кнопку (считаем, сколько людей отдали свой голос от региона)</b>
Что-то не работает? Пиши - @Serpus1"""


def get_reply_message_id(chat_id: int):
    row = db.get_data_from_db_first_row(f"select reply_message_id from region_chats where chat_id = {chat_id}")
    return row.get("reply_message_id")


def get_vote_count(chat_id: int):
    row = db.get_data_from_db_first_row(f"select count(*) from voters where chat_id = {chat_id}")
    return row.get("count(*)")


def get_last_message_id(chat_id: int):
    row = db.get_data_from_db_first_row(f"select last_message_id from region_chats where chat_id = {chat_id}")
    return row.get("last_message_id")


def set_last_message_id(chat_id, value):
    update_data(f"update region_chats set last_message_id = {value} where chat_id = {chat_id} ")


def set_reply_message_id(chat_id, value):
    update_data(f"update region_chats set reply_message_id = {value} where chat_id = {chat_id} ")
