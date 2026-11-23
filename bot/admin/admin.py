from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from backend.database import list_categories
from bot.admin.keyboards import (
    admin_analysis_keyboard,
    admin_home_keyboard,
    admin_mini_app_keyboard,
    admin_products_keyboard,
)

ADMIN_IDS = {8327989068}
router = Router(name="admin-panel")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def show_admin_welcome(message: Message, web_app_url: str) -> bool:
    """Show the admin welcome message and report whether the user is an admin."""
    user = message.from_user
    if user is None or not is_admin(user.id):
        return False

    await message.answer(
        f"Assalomu alaykum, admin {user.full_name}! 👋\n\n"
        "Admin panelni ochish uchun quyidagi tugmani bosing.",
        reply_markup=admin_mini_app_keyboard(web_app_url),
    )
    return True


@router.callback_query(
    F.data.in_(
        {
            "admin:products",
            "admin:analysis",
            "admin:home",
            "admin:category_analysis",
            "admin:product_analysis",
        }
    )
)
async def admin_callback_handler(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Bu boshqaruv bo'limi faqat adminlar uchun ochiq. Oddiy foydalanuvchi sifatida "
            "Mini App tugmasidan foydalanishingiz mumkin.",
            show_alert=True,
        )
        return

    action = (callback.data or "").removeprefix("admin:")
    if action == "products":
        await callback.message.edit_text(
            "Mahsulotlarni boshqarish bo'limiga xush kelibsiz. Kategoriya yoki yangi mahsulot "
            "qo'shish uchun quyidagi amallardan birini tanlang.",
            reply_markup=admin_products_keyboard(has_categories=bool(list_categories())),
        )
    elif action == "analysis":
        await callback.message.edit_text(
            "Tahlillar bo'limi ochildi. Kategoriyalar yoki alohida mahsulotlar bo'yicha "
            "ma'lumotlarni ko'rish uchun quyidagi variantlardan birini tanlang.",
            reply_markup=admin_analysis_keyboard(),
        )
    elif action == "home":
        await callback.message.edit_text(
            "Admin panelga qaytdingiz. Davom etish uchun mahsulotlar bo'limi yoki "
            "mahsulotlar tahlili bo'limidan birini tanlang.",
            reply_markup=admin_home_keyboard(),
        )
    else:
        action_labels = {
            "category_analysis": "Kategoriya tahlili",
            "product_analysis": "Mahsulot tahlili",
        }
        label = action_labels.get(action)
        if label is None:
            await callback.answer(
                "Bu tugma topilmadi yoki eskirgan bo'lishi mumkin. Iltimos, admin panelga "
                "qaytib, kerakli bo'limni qaytadan tanlang.",
                show_alert=True,
            )
            return

        await callback.message.edit_text(
            f"{label} bo'limi tanlandi. Hozircha bu sahifa namuna sifatida ko'rsatilmoqda; "
            "ma'lumot qo'shish va tahrirlash funksiyalari keyingi bosqichda ulanadi.",
            reply_markup=admin_analysis_keyboard(),
        )

    await callback.answer()