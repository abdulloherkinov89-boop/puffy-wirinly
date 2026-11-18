import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message
from backend.database import initialize_database, list_categories, save_user
from bot.admin.admin import router as admin_router, show_admin_welcome
from bot.admin.product_add import router as admin_product_router
from bot.keyboard.default_key import create_default_keyboard
from bot.keyboard.inline import create_inline_keyboard


def get_web_app_url() -> str:
    web_app_url = os.getenv(
        "WEB_APP_URL", "https://puffy-mini-app-web-production.up.railway.app/"
    ).strip()
    if not web_app_url:
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if railway_domain:
            web_app_url = f"https://{railway_domain}"
    if not web_app_url.startswith("https://"):
        raise RuntimeError(
            "WEB_APP_URL ni Railway domeningizning https:// manzili bilan sozlang"
        )
    return web_app_url


dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(admin_product_router)


@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    if user is None:
        return

    save_user(
        tg_id=user.id,
        full_name=user.full_name,
        first_name=user.first_name,
        username=user.username,
    )

    if await show_admin_welcome(message):
        return

    await message.answer(
        f"Assalomu alaykum, {user.full_name}! 👋\n\n"
        "Mini Appimizga xush kelibsiz! Menyuni ko'rish va buyurtma berish uchun quyidagi "
        "tugmani bosing. Telefon raqamingizni shu chatga yuborsangiz, uni profilingizga saqlaymiz.",
        reply_markup=create_inline_keyboard(get_web_app_url()),
    )


@dp.message(F.text, StateFilter(None))
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


@dp.message(F.contact, StateFilter(None))
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