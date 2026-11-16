from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def create_inline_keyboard(web_app_url: str) -> InlineKeyboardMarkup:
    """Create the inline Mini App launch button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Mini Appni ochish",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )
