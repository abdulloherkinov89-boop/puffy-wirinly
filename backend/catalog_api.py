import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from backend.database import (
    add_category,
    add_product,
    add_to_cart,
    get_cart,
    get_user,
    list_categories,
    list_products,
    remove_from_cart,
    save_user,
    update_cart_item,
)
from bot.admin.admin import is_admin

router = APIRouter(prefix="/api", tags=["catalog"])
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "frontend" / "uploads"


class TelegramAuthRequest(BaseModel):
    init_data: str


class CartItemRequest(BaseModel):
    init_data: str
    product_id: int
    quantity: int = 1


class CartRemoveRequest(BaseModel):
    init_data: str
    product_id: int


class AdminCategoryRequest(BaseModel):
    init_data: str
    name: str


class AdminProductRequest(BaseModel):
    init_data: str
    name: str
    price: int
    category_id: int
    about: str
    image_url: str | None = None
    image_data: str | None = None
    image_type: str | None = None


def validate_telegram_init_data(init_data: str) -> int:
    """Validate Telegram initData and return the authenticated Telegram user ID."""
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot is not configured")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", "")
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram initData hash is missing")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data.items())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=401, detail="Telegram initData is invalid")

    try:
        auth_date = int(data.get("auth_date", "0"))
        telegram_user = json.loads(data.get("user", "{}"))
        tg_id = int(telegram_user["id"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Telegram profile data is invalid")

    if auth_date > time.time() + 60 or time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Telegram login has expired")

    first_name = str(telegram_user.get("first_name") or "Telegram foydalanuvchisi")
    last_name = str(telegram_user.get("last_name") or "").strip()
    full_name = " ".join(part for part in (first_name, last_name) if part)
    username = telegram_user.get("username")
    save_user(
        tg_id=tg_id,
        full_name=full_name,
        first_name=first_name,
        username=str(username) if username else None,
    )
    return tg_id


def validate_admin_init_data(init_data: str) -> int:
    tg_id = validate_telegram_init_data(init_data)
    if not is_admin(tg_id):
        raise HTTPException(status_code=403, detail="Admin access is required")
    return tg_id


@router.post("/auth/telegram")
async def authenticate_telegram(payload: TelegramAuthRequest) -> dict[str, object]:
    tg_id = validate_telegram_init_data(payload.init_data)
    user = get_user(tg_id)
    if user is None:
        raise HTTPException(status_code=500, detail="Could not load Telegram profile")
    return {"authenticated": True, "user": user}


@router.get("/categories")
async def get_categories() -> list[dict[str, int | str]]:
    return list_categories()


@router.get("/products")
async def get_products() -> list[dict[str, int | str]]:
    return list_products()


@router.post("/admin/categories", status_code=201)
async def create_admin_category(payload: AdminCategoryRequest) -> dict[str, int | str]:
    validate_admin_init_data(payload.init_data)
    name = payload.name.strip()
    if not name or len(name) > 80:
        raise HTTPException(status_code=422, detail="Kategoriya nomi 1–80 ta belgidan iborat bo'lsin")
    try:
        category_id = add_category(name)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Bu kategoriya avval qo'shilgan")
    return {"id": category_id, "name": name}


@router.post("/admin/products", status_code=201)
async def create_admin_product(payload: AdminProductRequest) -> dict[str, int | str]:
    validate_admin_init_data(payload.init_data)
    name = payload.name.strip()
    about = payload.about.strip()
    if not name or len(name) > 120:
        raise HTTPException(status_code=422, detail="Mahsulot nomi 1–120 ta belgidan iborat bo'lsin")
    if payload.price <= 0:
        raise HTTPException(status_code=422, detail="Narx 0 dan katta bo'lishi kerak")
    if not about or len(about) > 1000:
        raise HTTPException(status_code=422, detail="Tavsif 1–1000 ta belgidan iborat bo'lsin")
    if payload.category_id <= 0 or payload.category_id not in {
        int(category["id"]) for category in list_categories()
    }:
        raise HTTPException(status_code=422, detail="Tanlangan kategoriya topilmadi")

    image_url = (payload.image_url or "").strip()
    if payload.image_data:
        if payload.image_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=422, detail="Rasm JPG, PNG yoki WebP formatida bo'lishi kerak")
        try:
            image_bytes = base64.b64decode(payload.image_data, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(status_code=422, detail="Rasm faylini o'qib bo'lmadi")
        if not image_bytes or len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Rasm hajmi 5 MB dan oshmasligi kerak")
        extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[payload.image_type]
        filename = f"{uuid4().hex}{extension}"
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        (UPLOADS_DIR / filename).write_bytes(image_bytes)
        image_url = f"/frontend/uploads/{filename}"
    else:
        parsed_image_url = urlparse(image_url)
        if parsed_image_url.scheme not in {"https", "http"} or not parsed_image_url.netloc:
            raise HTTPException(status_code=422, detail="Mahsulot uchun rasm yuklang yoki http/https rasm havolasini kiriting")

    try:
        product_id = add_product(
            name=name,
            price=payload.price,
            image_url=image_url,
            category_id=payload.category_id,
            about=about,
        )
    except IntegrityError:
        raise HTTPException(status_code=422, detail="Mahsulot saqlanmadi. Kategoriyani qayta tanlang")
    return {"id": product_id, "name": name}


@router.post("/cart/load")
async def load_cart(payload: TelegramAuthRequest) -> list[dict[str, int | str]]:
    tg_id = validate_telegram_init_data(payload.init_data)
    return get_cart(tg_id)


@router.post("/cart/add")
async def cart_add(payload: CartItemRequest) -> dict[str, bool]:
    tg_id = validate_telegram_init_data(payload.init_data)
    if payload.product_id <= 0:
        raise HTTPException(status_code=400, detail="Product ID is invalid")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    add_to_cart(tg_id=tg_id, product_id=payload.product_id, quantity=payload.quantity)
    return {"ok": True}


@router.post("/cart/update")
async def cart_update(payload: CartItemRequest) -> dict[str, bool]:
    tg_id = validate_telegram_init_data(payload.init_data)
    if payload.product_id <= 0:
        raise HTTPException(status_code=400, detail="Product ID is invalid")
    if payload.quantity <= 0:
        remove_from_cart(tg_id, payload.product_id)
    else:
        update_cart_item(tg_id=tg_id, product_id=payload.product_id, quantity=payload.quantity)
    return {"ok": True}


@router.post("/cart/remove")
async def cart_remove(payload: CartRemoveRequest) -> dict[str, bool]:
    tg_id = validate_telegram_init_data(payload.init_data)
    if payload.product_id <= 0:
        raise HTTPException(status_code=400, detail="Product ID is invalid")
    remove_from_cart(tg_id, payload.product_id)
    return {"ok": True}