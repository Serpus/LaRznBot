from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery


def register(dp: Dispatcher):
    @dp.callback_query(F.data == "user_voted")
    async def handle_vote_callback(callback: CallbackQuery):
        file_path = "resources/vote_count"
        count = 0
        try:
            # Читаем текущее значение
            with open(file_path, "r") as file:
                count = int(file.read().strip())
        except (FileNotFoundError, ValueError):
            pass

        # Увеличиваем счётчик
        count += 1

        # Записываем новое значение обратно
        with open(file_path, "w") as file:
            file.write(str(count))

        # Отправляем подтверждение пользователю (опционально)
        await callback.answer("Спасибо за ваш голос!", show_alert=True)
