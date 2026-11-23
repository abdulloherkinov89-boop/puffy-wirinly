from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def admin_mini_app_keyboard(web_app_url: str) -> InlineKeyboardMarkup:
    """Build the admin Mini App launch button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛠 Admin panelni ochish",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )


def admin_home_keyboard() -> InlineKeyboardMarkup:
    """Build the admin panel's main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin:products")],
            [InlineKeyboardButton(text="📊 Mahsulot tahlili", callback_data="admin:analysis")],
        ]
    )


def admin_analysis_keyboard() -> InlineKeyboardMarkup:
    """Build the admin analysis menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Kategoriya tahlili", callback_data="admin:category_analysis")],
            [InlineKeyboardButton(text="📈 Mahsulot tahlili", callback_data="admin:product_analysis")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")],
        ]
    )

