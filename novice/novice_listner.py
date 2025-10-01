import os
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

        download_file_from_yandex_disk()
        await save_to_excel(answers, message)
        upload_file_to_yandex_disk()

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

    def download_file_from_yandex_disk():
        """
        Скачивает файл с Яндекс.Диска.

        Returns:
            bool: True, если файл успешно скачан, иначе False.
        """
        disk_file_path = "Новички.xlsx"
        base_url = "https://cloud-api.yandex.net/v1/disk/resources/download"
        oauth_token = os.getenv("OAUTH")
        headers = {
            'Authorization': f'OAuth {oauth_token}'
        }

        # 1. Запросить URL для скачивания
        encoded_path = quote(disk_file_path, safe='')
        params = {'path': disk_file_path}

        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()  # Проверка на HTTP ошибки (4xx, 5xx)

            download_data = response.json()
            download_url = download_data.get('href')

            if not download_url:
                log("Ошибка: 'href' не найден в ответе API.")
                return False

        except requests.exceptions.RequestException as e:
            log(f"Ошибка при запросе URL для скачивания: {e}")
            return False
        except ValueError:  # Обработка ошибки при парсинге JSON
            log("Ошибка: Невозможно разобрать JSON-ответ при получении URL для скачивания.")
            return False

        # 2. Скачать файл по полученному URL
        try:
            # Важно: использовать тот же токен, что и в исходном запросе
            download_response = requests.get(download_url, headers=headers)
            download_response.raise_for_status()

            with open(file_xlsx_path, 'wb') as f:
                f.write(download_response.content)
            log(f"Файл успешно скачан: {file_xlsx_path}")
            return True

        except requests.exceptions.RequestException as e:
            log(f"Ошибка при скачивании файла: {e}")
            return False
        except IOError as e:
            log(f"Ошибка при сохранении файла локально: {e}")
            return False
        except Exception as e:
            log(f"Неизвестная ошибка: {e}")
            return False

    def upload_file_to_yandex_disk():
        """
        Загружает файл на Яндекс.Диск.
        Для получения токена: https://oauth.yandex.ru/authorize?response_type=token&client_id=<ClientID>
        """

        # 1. Подготовка: кодирование пути и формирование URL запроса с overwrite=true
        encoded_path = quote("Новички.xlsx", safe='')  # Кодируем путь для URL
        # Добавляем параметр overwrite=true к URL
        upload_url_request = f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={encoded_path}&overwrite=true"
        oauth_token = os.getenv("OAUTH")

        headers = {
            'Authorization': f'OAuth {oauth_token}'
        }

        try:
            # 2. Запрос URL для загрузки
            log("Запрашиваю URL для загрузки (с перезаписью)...")
            response_get_url = requests.get(upload_url_request, headers=headers)

            if response_get_url.status_code == 200:
                upload_data = response_get_url.json()
                upload_href = upload_data.get('href')

                if not upload_href:
                    log("Ошибка: Не получен URL для загрузки из ответа API.")
                    return

                log(f"Получен URL для загрузки (действителен 30 мин).")

                # 3. Загрузка файла по полученному URL
                log(f"Начинаю загрузку файла {file_xlsx_path} ...")
                with open(file_xlsx_path, 'rb') as file:
                    # Важно: Не указываем OAuth токен в заголовках для запроса на upload_href
                    response_upload = requests.put(upload_href, data=file)

                if response_upload.status_code in [201, 202]:  # 201 - создан, 202 - принят
                    log(f"Файл 'Новички.xlsx' успешно загружен (или перезаписан) на Яндекс.Диск.")
                else:
                    log(f"Ошибка при загрузке файла. Код ответа: {response_upload.status_code}")
                    log(f"Тело ответа: {response_upload.text}")

            elif response_get_url.status_code == 409:
                # Эта ошибка маловероятна с overwrite=true, но возможна в других сценариях
                log(f"Ошибка при запросе URL: {response_get_url.status_code}. "
                      f"Тело ответа: {response_get_url.text}")
            else:
                log(f"Ошибка при запросе URL для загрузки. Код ответа: {response_get_url.status_code}")
                log(f"Тело ответа: {response_get_url.text}")

        except requests.exceptions.RequestException as e:
            log(f"Произошла ошибка при выполнении запроса: {e}")
        except FileNotFoundError:
            log(f"Локальный файл '{file_xlsx_path}' не найден.")
        except Exception as e:
            log(f"Произошла непредвиденная ошибка: {e}")