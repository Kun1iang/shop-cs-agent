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

