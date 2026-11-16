from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def create_default_keyboard() -> ReplyKeyboardMarkup:
    """Create a reply keyboard for sharing the user's phone contact."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
