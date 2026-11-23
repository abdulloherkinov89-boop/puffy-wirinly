import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles

from bot.main import create_bot, run_bot
from backend.catalog_api import router as catalog_router
from backend.database import initialize_database

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_USERS_DIR = FRONTEND_DIR / "foydalanuvchilar"
FRONTEND_ADMIN_DIR = FRONTEND_DIR / "admin"
FRONTEND_HOME = FRONTEND_USERS_DIR / "home.html"
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


@app.get("/frontend/home.html")
async def legacy_home():
    return RedirectResponse(url="/foydalanuvchilar/home.html", status_code=302)


@app.get("/frontend/savat.html")
async def legacy_cart():
    return RedirectResponse(url="/foydalanuvchilar/savat.html", status_code=302)


@app.get("/frontend/buyurtmalarim.html")
async def legacy_orders():
    return RedirectResponse(url="/foydalanuvchilar/buyurtmalarim.html", status_code=302)


@app.get("/frontend/profile.html")
async def legacy_profile():
    return RedirectResponse(url="/foydalanuvchilar/profile.html", status_code=302)


app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def home():
    return FileResponse(FRONTEND_HOME)


@app.get("/admin")
async def admin_home():
    return FileResponse(FRONTEND_ADMIN_DIR / "admin_home.html")


@app.get("/admin/{page_name}")
async def admin_page(page_name: str):
    admin_pages = {
        "products": "admin_products.html",
        "orders": "admin_orders.html",
        "users": "admin_users.html",
    }
    file_name = admin_pages.get(page_name)
    if file_name is None:
        return Response(status_code=404)
    return FileResponse(FRONTEND_ADMIN_DIR / file_name)


@app.get("/foydalanuvchilar/{page_name}")
async def user_page(page_name: str):
    allowed_pages = {"home.html", "savat.html", "buyurtmalarim.html", "profile.html"}
    if page_name not in allowed_pages:
        return Response(status_code=404)
    return FileResponse(FRONTEND_USERS_DIR / page_name)


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