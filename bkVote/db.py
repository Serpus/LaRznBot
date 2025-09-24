import sqlite3
from bot_logger import log

db_name = "db/regions.db"


def get_data_from_db(select: str):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()

    log(f"Выполняем селект: {select}")
    cursor.execute(select)
    data = cursor.fetchall()

    # Получаем названия столбцов
    column_names = [description[0] for description in cursor.description]

    # Преобразуем данные в список словарей
    result = []
    for row in data:
        result.append(dict(zip(column_names, row)))

    connect.close()
    log(f"{result}")
    return result


def get_data_from_db_params(select: str, params):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()

    log(f"Выполняем селект: {select}")
    cursor.execute(select, params)
    data = cursor.fetchall()

    # Получаем названия столбцов
    column_names = [description[0] for description in cursor.description]

    # Преобразуем данные в список словарей
    result = []
    for row in data:
        result.append(dict(zip(column_names, row)))

    connect.close()
    log(f"{result}")
    return result


def get_data_from_db_first_row(select: str):
    """Возвращает первую строку как словарь {название_столбца: значение}"""
    with sqlite3.connect(db_name) as connect:
        cursor = connect.cursor()
        log(f"Выполняем селект: {select}")

        cursor.execute(select)
        row = cursor.fetchone()  # Получаем только первую строку

        if row is None:
            return None

        # Получаем названия столбцов
        column_names = [description[0] for description in cursor.description]

        # Возвращаем как словарь
        result = dict(zip(column_names, row))
        log(f"{result}")
        return result


def update_data(update_query: str):
    """
    Выполняет UPDATE-запрос к базе данных

    Args:
        update_query (str): SQL UPDATE-запрос

    Returns:
        int: Количество измененных строк
    """
    log(f"Обновляем данные: {update_query}")
    try:
        with sqlite3.connect(db_name) as connect:
            cursor = connect.cursor()
            cursor.execute(update_query)
            connect.commit()
            return cursor.rowcount  # Возвращает количество измененных строк

    except sqlite3.Error as e:
        log(f"Ошибка при обновлении данных: {e}")
        return 0


def add_voter(user_id, chat_id, user_name, user_login, vote_date):
    """Добавление голосующего в таблицу voters"""
    update_data(
        f"INSERT INTO voters (user_id, chat_id, user_name, user_login, vote_date) "
        f"VALUES ({user_id}, {chat_id}, '{user_name}', '{user_login}', '{vote_date}')")


def get_thread_id(chat_id):
    return get_data_from_db_first_row(f"select thread_id from region_chats where chat_id = {chat_id}").get("thread_id")

def get_chats():
    return get_data_from_db("select chat_id from region_chats")