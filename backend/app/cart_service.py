from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Cart, CartItem, Product, ProductVariant
from app.schemas import (
    CartItemSummary,
    CartProductSummary,
    CartSummary,
    CartVariantSummary,
)


class VariantUnavailableError(Exception):
    pass


class CartItemNotFoundError(Exception):
    pass


class CartQuantityError(Exception):
    pass


def cart_load_options():
    return (
        selectinload(Cart.items)
        .selectinload(CartItem.variant)
        .selectinload(ProductVariant.product)
        .selectinload(Product.images),
    )


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.scalar(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(*cart_load_options())
        .execution_options(populate_existing=True)
    )
    if cart is not None:
        return cart

    cart = Cart(user_id=user_id)
    db.add(cart)
    db.commit()
    return db.scalar(
        select(Cart)
        .where(Cart.id == cart.id)
        .options(*cart_load_options())
        .execution_options(populate_existing=True)
    )


def get_cart(db: Session, user_id: int) -> Cart:
    return db.scalar(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(*cart_load_options())
        .execution_options(populate_existing=True)
    )


def add_cart_item(
    db: Session,
    user_id: int,
    variant_id: int,
    quantity: int,
) -> Cart:
    if quantity < 1:
        raise CartQuantityError("数量必须大于 0")

    variant = db.scalar(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.is_active.is_(True),
        )
    )
    if variant is None:
        raise VariantUnavailableError("商品规格不存在或已下架")

    cart = get_or_create_cart(db, user_id)
    item = next(
        (item for item in cart.items if item.variant_id == variant_id),
        None,
    )
    new_quantity = quantity + (item.quantity if item else 0)
    if new_quantity > variant.stock:
        raise CartQuantityError(f"库存不足，当前最多可购买 {variant.stock} 件")

    if item is None:
        db.add(
            CartItem(
                cart_id=cart.id,
                variant_id=variant_id,
                quantity=quantity,
            )
        )
    else:
        item.quantity = new_quantity

    cart.updated_at = datetime.now(UTC)
    db.commit()
    return get_cart(db, user_id)


def update_cart_item(
    db: Session,
    user_id: int,
    item_id: int,
    quantity: int,
) -> Cart:
    if quantity < 1:
        raise CartQuantityError("数量必须大于 0")

    item = db.scalar(
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
        .options(selectinload(CartItem.variant))
    )
    if item is None:
        raise CartItemNotFoundError("购物车商品不存在")
    if quantity > item.variant.stock:
        raise CartQuantityError(
            f"库存不足，当前最多可购买 {item.variant.stock} 件"
        )

    item.quantity = quantity
    item.cart.updated_at = datetime.now(UTC)
    db.commit()
    return get_cart(db, user_id)


def delete_cart_item(db: Session, user_id: int, item_id: int) -> Cart:
    item = db.scalar(
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    if item is None:
        raise CartItemNotFoundError("购物车商品不存在")

    db.delete(item)
    db.commit()
    return get_cart(db, user_id)


def cart_to_summary(cart: Cart) -> CartSummary:
    items: list[CartItemSummary] = []
    for item in cart.items:
        product = item.variant.product
        primary_image = product.images[0].url if product.images else None
        items.append(
            CartItemSummary(
                id=item.id,
                quantity=item.quantity,
                unit_price_cents=item.variant.price_cents,
                line_total_cents=item.variant.price_cents * item.quantity,
                product=CartProductSummary(
                    id=product.id,
                    name=product.name,
                    slug=product.slug,
                    primary_image_url=primary_image,
                ),
                variant=CartVariantSummary(
                    id=item.variant.id,
                    name=item.variant.name,
                    sku=item.variant.sku,
                    price_cents=item.variant.price_cents,
                    stock=item.variant.stock,
                ),
            )
        )

    return CartSummary(
        id=cart.id,
        items=items,
        item_count=sum(item.quantity for item in cart.items),
        subtotal_cents=sum(
            item.variant.price_cents * item.quantity for item in cart.items
        ),
    )

