import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from backend.database import initialize_database, save_user
from bot.admin.a_key_inline import (
    admin_analysis_keyboard,
    admin_home_keyboard,
    admin_products_keyboard,
)
from bot.keyboard.default_key import create_default_keyboard
from bot.keyboard.inline import create_inline_keyboard

WEB_APP_URL = os.getenv(
    "WEB_APP_URL",
    os.getenv(
        "RENDER_EXTERNAL_URL",
        "https://puffy-wirinly.onrender.com",
    ),
).strip()
if not WEB_APP_URL.startswith("https://"):
    raise RuntimeError("WEB_APP_URL HTTPS manzil bo'lishi kerak")

dp = Dispatcher()
ADMIN_IDS = {8327989068}


@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    if user is None:
        return

    initialize_database()
    save_user(
        tg_id=user.id,
        full_name=user.full_name,
        first_name=user.first_name,
        username=user.username,
    )

    if user.id in ADMIN_IDS:
        await message.answer(
            f"Assalomu alaykum, admin {user.full_name}! 👋\n\n"
            "Admin panelga xush kelibsiz. Mahsulotlarni boshqarish yoki tahlillarni ko'rish uchun "
            "quyidagi bo'limlardan birini tanlang.",
            reply_markup=admin_home_keyboard(),
        )
        return

    await message.answer(
        f"Assalomu alaykum, {user.full_name}! 👋\n\n"
        "Mini Appimizga xush kelibsiz! Menyuni ko'rish va buyurtma berish uchun quyidagi "
        "tugmani bosing. Telefon raqamingizni shu chatga yuborsangiz, uni profilingizga saqlaymiz.",
        reply_markup=create_inline_keyboard(WEB_APP_URL),
    )


@dp.callback_query(F.data.startswith("admin:"))
async def admin_callback_handler(callback: CallbackQuery):
    user = callback.from_user
    if user.id not in ADMIN_IDS:
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
            reply_markup=admin_products_keyboard(),
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
            "add_category": "Kategoriya qo'shish",
            "add_product": "Mahsulot qo'shish",
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

        keyboard = (
            admin_analysis_keyboard()
            if action.endswith("_analysis")
            else admin_products_keyboard()
        )
        await callback.message.edit_text(
            f"{label} bo'limi tanlandi. Hozircha bu sahifa namuna sifatida ko'rsatilmoqda; "
            "ma'lumot qo'shish va tahrirlash funksiyalari keyingi bosqichda ulanadi.",
            reply_markup=keyboard,
        )

    await callback.answer()


@dp.message(F.text)
async def phone_text_handler(message: Message):
    user = message.from_user
    text = (message.text or "").strip()
    if user is None or not re.fullmatch(r"\+?[\d\s().-]{9,20}", text):
        return

    digits = re.sub(r"\D", "", text)
    if not 9 <= len(digits) <= 15:
        return

    phone_number = f"+{digits}" if text.startswith("+") else digits
    save_user(
        tg_id=user.id,
        full_name=user.full_name,
        first_name=user.first_name,
        username=user.username,
        phone_number=phone_number,
    )
    await message.answer(
        "Telefon raqamingiz profilingizga muvaffaqiyatli saqlandi. Rahmat! Endi Mini Appdagi "
        "buyurtmalaringizni rasmiylashtirishda ushbu raqamdan foydalanishingiz mumkin.",
        reply_markup=create_default_keyboard(),
    )


@dp.message(F.contact)
async def contact_handler(message: Message):
    user = message.from_user
    contact = message.contact
    if user is None or contact is None:
        return

    if contact.user_id != user.id:
        await message.answer(
            "Yuborilgan kontakt sizning raqamingiz emas ekan. Iltimos, xavfsizlik uchun "
            "Telegram profilingizga tegishli telefon raqamini yuboring."
        )
        return

    save_user(
        tg_id=user.id,
        full_name=user.full_name,
        first_name=user.first_name,
        username=user.username,
        phone_number=contact.phone_number,
    )
    await message.answer(
        "Telefon raqamingiz profilingizga muvaffaqiyatli saqlandi. Rahmat! Endi Mini Appdan "
        "foydalanib, buyurtmangizni qulay tarzda rasmiylashtirishingiz mumkin.",
        reply_markup=create_default_keyboard(),
    )


def create_bot() -> Bot:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi sozlanmagan")
    return Bot(token=token)


async def run_bot(bot: Bot) -> None:
    await dp.start_polling(bot, close_bot_session=False)


async def main() -> None:
    initialize_database()
    bot = create_bot()
    try:
        await run_bot(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())