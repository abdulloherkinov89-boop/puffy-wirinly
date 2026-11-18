from fastapi import APIRouter

from backend.database import list_categories, list_products

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories")
async def get_categories() -> list[dict[str, int | str]]:
    return list_categories()


@router.get("/products")
async def get_products() -> list[dict[str, int | str]]:
    return list_products()