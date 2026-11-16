
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_CALLBACK_PREFIX = "admin:"


def admin_home_keyboard() -> InlineKeyboardMarkup:
    """Show the admin entry point."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin:products")]
        ]
    )


def admin_products_keyboard() -> InlineKeyboardMarkup:
    """Show static product and category management actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin:add_category")],
            [InlineKeyboardButton(text="✏️ Kategoriyani tahrirlash", callback_data="admin:edit_category")],
            [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="admin:add_product")],
            [InlineKeyboardButton(text="✏️ Mahsulotni tahrirlash", callback_data="admin:edit_product")],
            [InlineKeyboardButton(text="📋 Mahsulotlar", callback_data="admin:list_products")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")],
        ]
    )
    