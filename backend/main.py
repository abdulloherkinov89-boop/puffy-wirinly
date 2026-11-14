import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bot.main import create_bot, run_bot
from backend.database import initialize_database

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_HOME = FRONTEND_DIR / "home.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    bot = create_bot()
    polling_task = asyncio.create_task(run_bot(bot), name="telegram-bot-polling")
    app.state.bot_polling_task = polling_task

    try:
        yield
    finally:
        polling_task.cancel()
        try:
            with suppress(asyncio.CancelledError):
                await polling_task
        finally:
            await bot.session.close()


app = FastAPI(lifespan=lifespan)
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def home():
    return FileResponse(FRONTEND_HOME)