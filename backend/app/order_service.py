from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.cart_service import get_cart
from app.models import Order, OrderItem, ProductVariant


class EmptyCartError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderStockError(Exception):
    pass


def order_load_options():
    return (selectinload(Order.items),)


def get_order(db: Session, user_id: int, order_no: str) -> Order:
    order = db.scalar(
        select(Order)
        .where(Order.order_no == order_no, Order.user_id == user_id)
        .options(*order_load_options())
    )
    if order is None:
        raise OrderNotFoundError("订单不存在")
    return order


def list_orders(db: Session, user_id: int) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .options(*order_load_options())
            .order_by(Order.created_at.desc(), Order.id.desc())
        ).all()
    )


def checkout(db: Session, user_id: int, idempotency_key: str) -> Order:
    existing = db.scalar(
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.idempotency_key == idempotency_key,
        )
        .options(*order_load_options())
    )
    if existing is not None:
        return existing

    cart = get_cart(db, user_id)
    if cart is None or not cart.items:
        raise EmptyCartError("购物车为空，无法结算")

    line_items: list[dict[str, int | str]] = []
    subtotal_cents = 0

    for cart_item in cart.items:
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == cart_item.variant_id
            )
        )
        if variant is None or not variant.is_active:
            raise OrderStockError("购物车中有商品规格已下架")
        if variant.stock < cart_item.quantity:
            raise OrderStockError(
                f"{variant.product.name} 库存不足，当前最多 {variant.stock} 件"
            )

        line_total_cents = variant.price_cents * cart_item.quantity
        subtotal_cents += line_total_cents
        line_items.append(
            {
                "product_id": variant.product_id,
                "variant_id": variant.id,
                "product_name": variant.product.name,
                "variant_name": variant.name,
                "sku": variant.sku,
                "unit_price_cents": variant.price_cents,
                "quantity": cart_item.quantity,
                "line_total_cents": line_total_cents,
            }
        )

    now = datetime.now(UTC)
    order = Order(
        order_no=f"ORD{now:%Y%m%d%H%M%S}{uuid4().hex[:6].upper()}",
        user_id=user_id,
        status="paid",
        subtotal_cents=subtotal_cents,
        shipping_fee_cents=0,
        total_cents=subtotal_cents,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.flush()

    for line_item in line_items:
        db.add(OrderItem(order_id=order.id, **line_item))
        variant = db.get(ProductVariant, line_item["variant_id"])
        variant.stock -= int(line_item["quantity"])

    for cart_item in list(cart.items):
        db.delete(cart_item)

    db.commit()
    return get_order(db, user_id, order.order_no)

