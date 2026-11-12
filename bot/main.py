import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi sozlanmagan")

WEB_APP_URL = "https://abdulloherkinov89-boop.github.io/puffy-wirinly/"

bot = Bot(token=TOKEN)
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


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())