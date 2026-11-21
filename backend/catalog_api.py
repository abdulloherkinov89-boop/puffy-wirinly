import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import (
    add_to_cart,
    get_cart,
    get_user,
    list_categories,
    list_products,
    remove_from_cart,
    save_user,
    update_cart_item,
)

router = APIRouter(prefix="/api", tags=["catalog"])


class TelegramAuthRequest(BaseModel):
    init_data: str


class CartItemRequest(BaseModel):
    init_data: str
    product_id: int
    quantity: int = 1


class CartRemoveRequest(BaseModel):
    init_data: str
    product_id: int


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