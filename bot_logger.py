import logging
import os
from datetime import datetime

# Создаем логгер
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Форматтеры
formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
formatter_user = logging.Formatter("%(asctime)s [%(levelname)s]: [@%(user)s] %(message)s")

def check_folder():
    """Проверяет и создает папку для логов, если она не существует."""
    dir_name = "logs"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


class UserFilter(logging.Filter):
    """
    Добавляет поле 'user' в запись лога.
    Если пользователь не указан, используется значение по умолчанию ('Anonymous').
    """
    def __init__(self, user=None):
        super().__init__()
        self.user = user

    def filter(self, record):
        # Добавляем поле 'user' в запись лога
        record.user = self.user or getattr(record, 'user', 'Anonymous')
        return True


def log(text: str):
    """Логирует сообщение без информации о пользователе."""
    date = datetime.now().strftime("%d-%m-%Y")

    check_folder()
    filename = f"logs/{date}_logs.txt"

    # Обработчики
    file_handler = logging.FileHandler(filename, "a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Очистка старых обработчиков и добавление новых
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(text)


def log_user(text: str, user: str):
    """Логирует сообщение с информацией о пользователе."""
    date = datetime.now().strftime("%d-%m-%Y")

    check_folder()
    filename = f"logs/{date}_logs.txt"

    # Обработчики
    file_handler = logging.FileHandler(filename, "a", encoding="utf-8")
    file_handler.setFormatter(formatter_user)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_user)
    console_handler.setLevel(logging.DEBUG)

    # Добавляем фильтр для пользователя
    user_filter = UserFilter(user=user)
    file_handler.addFilter(user_filter)
    console_handler.addFilter(user_filter)

    # Очистка старых обработчиков и добавление новых
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(text)
