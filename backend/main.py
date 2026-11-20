import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from bot.main import create_bot, run_bot
from backend.catalog_api import router as catalog_router
from backend.database import initialize_database

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_HOME = FRONTEND_DIR / "home.html"
UPLOADS_DIR = FRONTEND_DIR / "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


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
app.include_router(catalog_router)
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def home():
    return FileResponse(FRONTEND_HOME)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


@app.head("/")
async def home_health_check():
    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )