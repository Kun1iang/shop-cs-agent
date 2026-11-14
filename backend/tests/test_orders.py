from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, ProductVariant


def get_variant_id(client: TestClient, slug: str) -> int:
    response = client.get(f"/api/v1/products/{slug}")
    assert response.status_code == 200
    return response.json()["variants"][0]["id"]


def add_to_cart(client: TestClient, variant_id: int, quantity: int = 1) -> None:
    response = client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": quantity},
    )
    assert response.status_code == 200


def checkout(
    client: TestClient,
    idempotency_key: str | None = None,
):
    return client.post(
        "/api/v1/orders/checkout",
        headers={"Idempotency-Key": idempotency_key or uuid4().hex},
    )


def test_checkout_creates_paid_order_and_clears_cart(
    client: TestClient,
    db_session: Session,
) -> None:
    variant_id = get_variant_id(client, "gan-charger-65w")
    add_to_cart(client, variant_id, quantity=2)
    stock_before = db_session.get(ProductVariant, variant_id).stock

    response = checkout(client)

    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "paid"
    assert order["total_cents"] == 29800
    assert order["items"][0]["product_name"] == "65W 氮化镓充电器"
    assert order["items"][0]["quantity"] == 2

    cart = client.get("/api/v1/cart").json()
    assert cart["item_count"] == 0

    db_session.expire_all()
    assert db_session.get(ProductVariant, variant_id).stock == stock_before - 2


def test_checkout_empty_cart_is_rejected(client: TestClient) -> None:
    response = checkout(client)

    assert response.status_code == 400
    assert "购物车为空" in response.json()["detail"]


def test_checkout_is_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    variant_id = get_variant_id(client, "magnetic-phone-stand")
    add_to_cart(client, variant_id)
    key = "checkout-test-key-001"
    stock_before = db_session.get(ProductVariant, variant_id).stock

    first = checkout(client, key)
    second = checkout(client, key)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["order_no"] == second.json()["order_no"]

    db_session.expire_all()
    assert db_session.get(ProductVariant, variant_id).stock == stock_before - 1
    orders = db_session.scalars(select(Order)).all()
    assert len(orders) == 1


def test_checkout_rejects_stale_stock(
    client: TestClient,
    db_session: Session,
) -> None:
    variant_id = get_variant_id(client, "folding-desk-fan")
    add_to_cart(client, variant_id, quantity=2)
    variant = db_session.get(ProductVariant, variant_id)
    variant.stock = 1
    db_session.commit()

    response = checkout(client)

    assert response.status_code == 409
    assert "库存不足" in response.json()["detail"]


def test_order_list_and_detail(client: TestClient) -> None:
    variant_id = get_variant_id(client, "a5-hardcover-notebook")
    add_to_cart(client, variant_id)
    created = checkout(client).json()

    listed = client.get("/api/v1/orders")
    assert listed.status_code == 200
    assert listed.json()[0]["order_no"] == created["order_no"]

    detail = client.get(f"/api/v1/orders/{created['order_no']}")
    assert detail.status_code == 200
    assert detail.json()["items"][0]["sku"] == "NOTEBOOK-A5-BEIGE"

    missing = client.get("/api/v1/orders/ORD-NOT-FOUND")
    assert missing.status_code == 404
