import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)
from backend.database import initialize_database, save_user

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

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon raqamni yuborish",
                    request_contact=True,
                )
            ],
            [
                KeyboardButton(
                    text="🚀 Mini Appni ochish",
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Mini Appimizga xush kelibsiz!",
        reply_markup=keyboard
    )


@dp.message(F.contact)
async def contact_handler(message: Message):
    user = message.from_user
    contact = message.contact
    if user is None or contact is None:
        return

    if contact.user_id != user.id:
        await message.answer("Iltimos, o'zingizning telefon raqamingizni yuboring.")
        return

    save_user(
        tg_id=user.id,
        full_name=user.full_name,
        first_name=user.first_name,
        username=user.username,
        phone_number=contact.phone_number,
    )
    await message.answer("Telefon raqamingiz saqlandi. Rahmat!")


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