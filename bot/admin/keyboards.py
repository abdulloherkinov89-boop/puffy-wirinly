from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_home_keyboard() -> InlineKeyboardMarkup:
    """Build the admin panel's main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin:products")],
            [InlineKeyboardButton(text="📊 Mahsulot tahlili", callback_data="admin:analysis")],
        ]
    )


def admin_products_keyboard(has_categories: bool = True) -> InlineKeyboardMarkup:
    """Build product controls, enabling product creation when categories exist."""
    buttons = [
        [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin:add_category")]
    ]
    if has_categories:
        buttons.append(
            [InlineKeyboardButton(text="➕ Mahsulot qo'shish", callback_data="admin:add_product")]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_analysis_keyboard() -> InlineKeyboardMarkup:
    """Build the admin analysis menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Kategoriya tahlili", callback_data="admin:category_analysis")],
            [InlineKeyboardButton(text="📈 Mahsulot tahlili", callback_data="admin:product_analysis")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:home")],
        ]
    )


def admin_cancel_keyboard() -> InlineKeyboardMarkup:
    """Build the cancel button used by admin forms."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Bekor qilish", callback_data="admin:cancel")]
        ]
    )


def category_selection_keyboard(categories: list[dict[str, int | str]]) -> InlineKeyboardMarkup:
    """Build an inline keyboard for selecting a product category."""
    buttons = [
        [
            InlineKeyboardButton(
                text=str(category["name"]),
                callback_data=f"admin:pick_category:{category['id']}",
            )
        ]
        for category in categories
    ]
    buttons.append(
        [InlineKeyboardButton(text="✖️ Bekor qilish", callback_data="admin:cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)