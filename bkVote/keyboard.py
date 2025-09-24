from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_vote_button_keyboard():
    """
    Создаёт инлайн-клавиатуру с одной кнопкой 'Я проголосовал!'.
    Callback data используется для идентификации нажатия.
    """
    button = InlineKeyboardButton(text="Я проголосовал!", callback_data="user_voted")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    return keyboard