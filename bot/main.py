import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)

WEB_APP_URL = os.getenv(
    "WEB_APP_URL",
    os.getenv(
        "RENDER_EXTERNAL_URL",
        "https://abdulloherkinov89-boop.github.io/puffy-wirinly/",
    ),
).strip()
if not WEB_APP_URL.startswith("https://"):
    raise RuntimeError("WEB_APP_URL HTTPS manzil bo'lishi kerak")

dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
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


def create_bot() -> Bot:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi sozlanmagan")
    return Bot(token=token)


async def run_bot(bot: Bot) -> None:
    await dp.start_polling(bot, close_bot_session=False)


async def main() -> None:
    bot = create_bot()
    try:
        await run_bot(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())