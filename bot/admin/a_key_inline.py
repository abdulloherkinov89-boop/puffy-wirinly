
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_CALLBACK_PREFIX = "admin:"


def admin_home_keyboard() -> InlineKeyboardMarkup:
    """Show the two main admin sections."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin:products")],
            [InlineKeyboardButton(text="📊 Mahsulot tahlili", callback_data="admin:analysis")],
        ]
    )


def admin_products_keyboard(has_categories: bool = True) -> InlineKeyboardMarkup:
    """Show product creation only when at least one category exists."""
    actions = [
        [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin:add_category")]
    ]
    if has_categories:
        actions.append(
            [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="admin:add_product")]
        )
    actions.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")])
    return InlineKeyboardMarkup(
        inline_keyboard=actions
    )


def admin_analysis_keyboard() -> InlineKeyboardMarkup:
    """Show static category and product analysis actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Kategoriya tahlili", callback_data="admin:category_analysis")],
            [InlineKeyboardButton(text="📈 Mahsulot tahlili", callback_data="admin:product_analysis")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")],
        ]
    )
    