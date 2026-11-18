import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from backend.database import add_category, add_product, list_categories
from bot.admin.admin import is_admin
from bot.admin.keyboards import (
    admin_cancel_keyboard,
    admin_home_keyboard,
    category_selection_keyboard,
)

router = Router(name="admin-product-add")
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "frontend" / "uploads"


class CategoryForm(StatesGroup):
    name = State()


class ProductForm(StatesGroup):
    name = State()
    price = State()
    image = State()
    category_id = State()
    about = State()


@router.callback_query(F.data == "admin:add_category")
async def start_category_form(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Bu amal faqat admin uchun.", show_alert=True)
        return

    await state.clear()
    await state.set_state(CategoryForm.name)
    await callback.message.edit_text(
        "Yangi kategoriya nomini yuboring:", reply_markup=admin_cancel_keyboard()
    )
    await callback.answer()


@router.message(CategoryForm.name)
async def save_category(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        return

    name = (message.text or "").strip()
    if not name or len(name) > 80:
        await message.answer("Kategoriya nomi 1–80 ta belgidan iborat bo'lsin.")
        return

    try:
        add_category(name)
    except sqlite3.IntegrityError:
        await message.answer("Bu kategoriya avval qo'shilgan. Boshqa nom kiriting.")
        return

    await state.clear()
    await message.answer(
        f"✅ «{name}» kategoriyasi qo'shildi.", reply_markup=admin_home_keyboard()
    )


@router.callback_query(F.data == "admin:add_product")
async def start_product_form(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Bu amal faqat admin uchun.", show_alert=True)
        return

    if not list_categories():
        await callback.answer(
            "Avval kategoriya qo'shing. Kategoriyasiz mahsulot qo'shib bo'lmaydi.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.set_state(ProductForm.name)
    await callback.message.edit_text(
        "Mahsulot nomini yuboring:", reply_markup=admin_cancel_keyboard()
    )
    await callback.answer()


@router.message(ProductForm.name)
async def product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name or len(name) > 120:
        await message.answer("Mahsulot nomi 1–120 ta belgidan iborat bo'lsin.")
        return

    await state.update_data(name=name)
    await state.set_state(ProductForm.price)
    await message.answer("Mahsulot narxini so'mda yuboring (masalan: 25000):")


@router.message(ProductForm.price)
async def product_price(message: Message, state: FSMContext) -> None:
    raw_price = (message.text or "").strip()
    if not re.fullmatch(r"[\d\s.,]+", raw_price):
        await message.answer("Narxni faqat raqam bilan yuboring, masalan: 25000.")
        return

    price = int(re.sub(r"\D", "", raw_price) or "0")
    if price <= 0:
        await message.answer("Narx 0 dan katta bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(price=price)
    await state.set_state(ProductForm.image)
    await message.answer(
        "Mahsulot rasmini Telegram orqali yuboring yoki rasmning http/https linkini yuboring:"
    )


@router.message(ProductForm.image)
async def product_image(message: Message, state: FSMContext) -> None:
    if message.photo:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        photo = message.photo[-1]
        telegram_file = await message.bot.get_file(photo.file_id)
        extension = Path(telegram_file.file_path or "").suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            extension = ".jpg"

        filename = f"{uuid4().hex}{extension}"
        destination = UPLOADS_DIR / filename
        await message.bot.download_file(telegram_file.file_path, destination=destination)
        image_url = f"/frontend/uploads/{filename}"
    else:
        image_url = (message.text or "").strip()
        parsed_url = urlparse(image_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            await message.answer("Yuboring: rasm (photo) yoki to'g'ri http/https rasm linki.")
            return

    await state.update_data(image_url=image_url)
    await state.set_state(ProductForm.category_id)
    await message.answer(
        "Mahsulot kategoriyasini tanlang:",
        reply_markup=category_selection_keyboard(list_categories()),
    )


@router.callback_query(F.data.startswith("admin:pick_category:"))
async def product_category(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Bu amal faqat admin uchun.", show_alert=True)
        return

    if await state.get_state() != ProductForm.category_id.state:
        await callback.answer(
            "Bu tanlov eskirgan. Mahsulot qo'shishni qaytadan boshlang.", show_alert=True
        )
        return

    try:
        category_id = int((callback.data or "").rsplit(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Kategoriya tanlovi noto'g'ri.", show_alert=True)
        return

    category_ids = {int(category["id"]) for category in list_categories()}
    if category_id not in category_ids:
        await callback.answer("Bu kategoriya topilmadi. Qaytadan tanlang.", show_alert=True)
        return

    await state.update_data(category_id=category_id)
    await state.set_state(ProductForm.about)
    await callback.message.edit_text(
        "Mahsulot haqida qisqacha ma'lumot yuboring:",
        reply_markup=admin_cancel_keyboard(),
    )
    await callback.answer()


@router.message(ProductForm.about)
async def save_product(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        return

    about = (message.text or "").strip()
    if not about or len(about) > 1000:
        await message.answer("Mahsulot haqida 1–1000 ta belgida yozing.")
        return

    data = await state.get_data()
    add_product(
        name=data["name"],
        price=data["price"],
        image_url=data["image_url"],
        category_id=data["category_id"],
        about=about,
    )
    await state.clear()
    await message.answer(
        f"✅ «{data['name']}» mahsuloti bazaga saqlandi.",
        reply_markup=admin_home_keyboard(),
    )


@router.callback_query(F.data == "admin:cancel")
async def cancel_form(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Bu amal faqat admin uchun.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Admin panelga qaytdingiz.", reply_markup=admin_home_keyboard()
    )
    await callback.answer("Bekor qilindi")