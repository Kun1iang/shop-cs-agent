from fastapi.testclient import TestClient


def test_list_products_returns_six_seeded_products(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) == 6
    assert {product["category"]["name"] for product in products} == {
        "数码配件",
        "桌面小电器",
        "办公文具",
    }


def test_list_products_filters_by_category(client: TestClient) -> None:
    response = client.get(
        "/api/v1/products",
        params={"category": "digital-accessories"},
    )

    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    assert all(
        product["category"]["slug"] == "digital-accessories"
        for product in products
    )


def test_get_product_detail(client: TestClient) -> None:
    response = client.get("/api/v1/products/gan-charger-65w")

    assert response.status_code == 200
    product = response.json()
    assert product["name"] == "65W 氮化镓充电器"
    assert product["price_from_cents"] == 14900
    assert product["variants"][0]["sku"] == "CHARGER-65W-WHITE"


def test_unknown_product_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/products/not-found")

    assert response.status_code == 404
    assert response.json() == {"detail": "商品不存在"}
