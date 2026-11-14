from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Category, Product
from app.schemas import ProductDetail, ProductSummary

router = APIRouter(prefix="/api/v1/products", tags=["products"])
DbSession = Annotated[Session, Depends(get_db)]


def product_load_options():
    return (
        selectinload(Product.category),
        selectinload(Product.variants),
        selectinload(Product.images),
    )


@router.get("", response_model=list[ProductSummary])
def list_products(
    db: DbSession,
    category: Annotated[str | None, Query()] = None,
) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.status == "active")
        .options(*product_load_options())
        .order_by(Product.id)
    )

    if category:
        statement = statement.join(Product.category).where(
            Category.slug == category
        )

    return list(db.scalars(statement).all())


@router.get("/{slug}", response_model=ProductDetail)
def get_product(slug: str, db: DbSession) -> Product:
    product = db.scalar(
        select(Product)
        .where(Product.slug == slug, Product.status == "active")
        .options(*product_load_options())
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在",
        )

    return product

