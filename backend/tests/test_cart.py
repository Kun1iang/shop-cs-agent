from fastapi.testclient import TestClient


def get_variant_id(client: TestClient, slug: str) -> int:
    response = client.get(f"/api/v1/products/{slug}")
    assert response.status_code == 200
    return response.json()["variants"][0]["id"]


def test_cart_starts_empty(client: TestClient) -> None:
    response = client.get("/api/v1/cart")

    assert response.status_code == 200
    assert response.json()["item_count"] == 0
    assert response.json()["subtotal_cents"] == 0


def test_add_same_variant_merges_quantity(client: TestClient) -> None:
    variant_id = get_variant_id(client, "gan-charger-65w")

    first = client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 1},
    )
    second = client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 2},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    cart = second.json()
    assert cart["item_count"] == 3
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3
    assert cart["subtotal_cents"] == 14900 * 3


def test_add_more_than_stock_is_rejected(client: TestClient) -> None:
    variant_id = get_variant_id(client, "mini-humidifier")

    response = client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 999},
    )

    assert response.status_code == 400
    assert "库存不足" in response.json()["detail"]


def test_update_and_delete_cart_item(client: TestClient) -> None:
    variant_id = get_variant_id(client, "a5-hardcover-notebook")
    added = client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 1},
    )
    assert added.status_code == 200
    added = added.json()
    item_id = added["items"][0]["id"]

    updated = client.patch(
        f"/api/v1/cart/items/{item_id}",
        json={"quantity": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["items"][0]["quantity"] == 2

    deleted = client.delete(f"/api/v1/cart/items/{item_id}")
    assert deleted.status_code == 204

    empty_cart = client.get("/api/v1/cart").json()
    assert empty_cart["item_count"] == 0

