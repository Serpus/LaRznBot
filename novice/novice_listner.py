import sqlite3

import openpyxl
import requests
from aiogram import types, F, Router
from aiogram.types import ReactionTypeEmoji
from urllib.parse import quote

from bot_logger import log

file_xlsx_path = "novice/Новички.xlsx"

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
        # upload_file_to_yandex_disk()
        await message.react(reaction=[ReactionTypeEmoji(emoji="👾")])

    async def save_to_excel(answers, message: types.Message):
        full_name = answers.get("Фамилия Имя Отчество", "")
        location = answers.get("Населенный пункт (город, поселок+район, деревня+район)", "")
        phone = answers.get("Телефон (просьба писать через 8, без пробелов)", "")
        telegram = answers.get("Ссылка на телеграм", "")

        try:
            # Открываем файл или создаём новый
            wb = openpyxl.load_workbook(file_xlsx_path)
        except FileNotFoundError as e:
            log(f"Не удалось найти файл {file_xlsx_path}")
            await message.react(reaction=[ReactionTypeEmoji(emoji="😡")])
            raise e
        ws = wb.active
        ws.append([None, location, full_name, "", int(phone), telegram])
        wb.save(file_xlsx_path)

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

    def upload_file_to_yandex_disk(oauth_token):
        """
        Загружает файл на Яндекс.Диск.

        :param oauth_token: OAuth-токен для доступа к Яндекс.Диску.
        """
        # 1. Подготовка: кодирование пути и формирование URL запроса с overwrite=true
        encoded_path = quote("Новички.xlsx", safe='')  # Кодируем путь для URL
        # Добавляем параметр overwrite=true к URL
        upload_url_request = f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={encoded_path}&overwrite=true"

        headers = {
            'Authorization': f'OAuth {oauth_token}'
        }

        try:
            # 2. Запрос URL для загрузки
            print("Запрашиваю URL для загрузки (с перезаписью)...")
            response_get_url = requests.get(upload_url_request, headers=headers)

            if response_get_url.status_code == 200:
                upload_data = response_get_url.json()
                upload_href = upload_data.get('href')

                if not upload_href:
                    print("Ошибка: Не получен URL для загрузки из ответа API.")
                    return

                print(f"Получен URL для загрузки (действителен 30 мин).")

                # 3. Загрузка файла по полученному URL
                print(f"Начинаю загрузку файла {file_xlsx_path} ...")
                with open(file_xlsx_path, 'rb') as file:
                    # Важно: Не указываем OAuth токен в заголовках для запроса на upload_href
                    response_upload = requests.put(upload_href, data=file)

                if response_upload.status_code in [201, 202]:  # 201 - создан, 202 - принят
                    print(f"Файл 'Новички.xlsx' успешно загружен (или перезаписан) на Яндекс.Диск.")
                else:
                    print(f"Ошибка при загрузке файла. Код ответа: {response_upload.status_code}")
                    print(f"Тело ответа: {response_upload.text}")

            elif response_get_url.status_code == 409:
                # Эта ошибка маловероятна с overwrite=true, но возможна в других сценариях
                print(f"Ошибка при запросе URL: {response_get_url.status_code}. "
                      f"Тело ответа: {response_get_url.text}")
            else:
                print(f"Ошибка при запросе URL для загрузки. Код ответа: {response_get_url.status_code}")
                print(f"Тело ответа: {response_get_url.text}")

        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка при выполнении запроса: {e}")
        except FileNotFoundError:
            print(f"Локальный файл '{file_xlsx_path}' не найден.")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")