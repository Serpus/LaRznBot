from bot_logger import log

chat_id_slujebka = -1003043852228
vote_link = "https://burgerkingapp.onelink.me/220f/g4k9umfa"
short_vote_link = "https://clck.ru/3PHUak"
bk_instruction_post = "https://t.me/lizaalertryazan/7684/7685"

# -1001635093935 - реальный чат ЛА
# -1002911410297 - тестовый чат
la_chat_id = -1001635093935
# 7684 - реальная тема с БК голосованием
# 4 - тестовая тема
bk_thread_id = 7684


def generate_daily_message():
    vote_count = get_vote_count()
    return f"""Напоминаем, что <b>голосовать можно каждый день</b>
Сегодня новый день и новая возможность помочь отряду

<u>Самый энергичный по голосованию регион оденется в отрядную форму!</u>

Ссылка для голосования: {short_vote_link}
Полная инструкция с видео: {bk_instruction_post}

<i>Мы проголосовали: {vote_count} раз(а)</i>

<b>Проголосовал - нажми кнопку (работает раз в день)</b>"""

def get_reply_message_id():
    try:
        with open("resources/reply_message_id", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        log("Не удаётся найти файл reply_message_id")


def get_vote_count():
    try:
        with open("resources/vote_count", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        log("Не удаётся найти файл vote_count")


def get_last_message_id():
    try:
        with open("resources/last_message_id", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        log("Не удаётся найти файл last_message_id")


def set_last_message_id(value):
    try:
        with open("resources/last_message_id", "w") as f:
            f.write(str(value))
    except (FileNotFoundError, ValueError):
        log("Не удаётся записать значение в файл last_message_id")


def set_reply_message_id(value):
    try:
        with open("resources/reply_message_id", "w") as f:
            f.write(str(value))
    except (FileNotFoundError, ValueError):
        log("Не удаётся записать значение в файл reply_message_id")