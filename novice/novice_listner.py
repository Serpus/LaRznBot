import sqlite3

import openpyxl
from aiogram import types, F, Router
from aiogram.types import ReactionTypeEmoji

from bot_logger import log


def register(router: Router):
    @router.message(F.text.startswith("Новый ответ в опросе: Анкета добровольца ДПСО"))
    async def handler(message: types.Message):
        lines = message.text.strip().split('\n')
        answers = {}
        current_q = None
        for line in lines:
            line = line.strip()
            if line.startswith("Q:"):
                current_q = line[3:].strip()
            elif line.startswith("A:"):
                answers[current_q] = line[3:].strip()
        log(f"Новая анкета: {answers}")
        save_to_db(answers)
        await save_to_excel(answers, message)
        await message.react(reaction=[ReactionTypeEmoji(emoji="👾")])

    async def save_to_excel(answers, message: types.Message):
        full_name = answers.get("Фамилия Имя Отчество", "")
        location = answers.get("Населенный пункт (город, поселок+район, деревня+район)", "")
        phone = answers.get("Телефон (просьба писать через 8, без пробелов)", "")
        telegram = answers.get("Ссылка на телеграм", "")

        file_name = "novice/Новички.xlsx"
        try:
            # Открываем файл или создаём новый
            wb = openpyxl.load_workbook(file_name)
        except FileNotFoundError as e:
            log(f"Не удалось найти файл {file_name}")
            await message.react(reaction=[ReactionTypeEmoji(emoji="😡")])
            raise e
        ws = wb.active
        ws.append([None, location, full_name, "", int(phone), telegram])
        wb.save(file_name)

    def save_to_db(answers):
        conn = sqlite3.connect("db/novice.db")
        try:
            cursor = conn.cursor()

            full_name = answers.get("Фамилия Имя Отчество", "")
            age = answers.get("Вам есть 18 лет?", "")
            location = answers.get("Населенный пункт (город, поселок+район, деревня+район)", "")
            phone = answers.get("Телефон (просьба писать через 8, без пробелов)", "")
            telegram = answers.get("Ссылка на телеграм", "")
            has_car = answers.get("Наличие авто", "")
            previous_searches = answers.get("Участвовали ли Вы ранее в поисках пропавших?", "")
            help_types = answers.get("Варианты помощи", "")
            how_learned = answers.get("Как вы узнали об отряде?", "")
            other_info = answers.get("По желанию, напишите то, что хотели бы рассказать о себе, чего нет в анкете", "")

            cursor.execute('''
                    INSERT INTO novice (full_name, age, location, phone, telegram, has_car, previous_searches, help_types, how_learned, other_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (full_name, age, location, phone, telegram, has_car, previous_searches, help_types, how_learned,
                      other_info))

            conn.commit()
        finally:
            conn.close()
