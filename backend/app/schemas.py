from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class VariantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    price_cents: int
    stock: int
    is_active: bool


class ProductImageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    alt: str


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    summary: str
    primary_image_url: str | None
    price_from_cents: int
    stock_total: int
    category: CategorySummary
    variants: list[VariantSummary]


class ProductDetail(ProductSummary):
    description: str
    images: list[ProductImageSummary]


class AddCartItem(BaseModel):
    variant_id: int
    quantity: int


class UpdateCartItem(BaseModel):
    quantity: int


class CartProductSummary(BaseModel):
    id: int
    name: str
    slug: str
    primary_image_url: str | None


class CartVariantSummary(BaseModel):
    id: int
    name: str
    sku: str
    price_cents: int
    stock: int


class CartItemSummary(BaseModel):
    id: int
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    product: CartProductSummary
    variant: CartVariantSummary


class CartSummary(BaseModel):
    id: int
    items: list[CartItemSummary]
    item_count: int
    subtotal_cents: int


class OrderItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int
    product_name: str
    variant_name: str
    sku: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    status: str
    subtotal_cents: int
    shipping_fee_cents: int
    total_cents: int
    created_at: datetime
    items: list[OrderItemSummary]


