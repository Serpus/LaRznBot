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