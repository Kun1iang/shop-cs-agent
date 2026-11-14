from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Category, Product, ProductImage, ProductVariant

CATEGORY_SEEDS = [
    {"name": "数码配件", "slug": "digital-accessories", "sort_order": 1},
    {"name": "桌面小电器", "slug": "desktop-appliances", "sort_order": 2},
    {"name": "办公文具", "slug": "office-stationery", "sort_order": 3},
]

PRODUCT_SEEDS = [
    {
        "category_slug": "digital-accessories",
        "name": "65W 氮化镓充电器",
        "slug": "gan-charger-65w",
        "summary": "小巧机身，支持多设备快充。",
        "description": "65W 氮化镓充电器，适合桌面办公和出差使用。",
        "variants": [
            {
                "name": "白色",
                "sku": "CHARGER-65W-WHITE",
                "price_cents": 14900,
                "stock": 36,
            }
        ],
    },
    {
        "category_slug": "digital-accessories",
        "name": "磁吸手机支架",
        "slug": "magnetic-phone-stand",
        "summary": "可折叠磁吸结构，横竖屏自由切换。",
        "description": "铝合金磁吸手机支架，适合桌面视频和日常办公。",
        "variants": [
            {
                "name": "深空灰",
                "sku": "STAND-MAG-GRAY",
                "price_cents": 5900,
                "stock": 48,
            },
            {
                "name": "银色",
                "sku": "STAND-MAG-SILVER",
                "price_cents": 5900,
                "stock": 28,
            },
        ],
    },
    {
        "category_slug": "desktop-appliances",
        "name": "迷你桌面加湿器",
        "slug": "mini-humidifier",
        "summary": "低噪细雾，适合小空间桌面使用。",
        "description": "300ml 迷你桌面加湿器，带暖光氛围灯。",
        "variants": [
            {
                "name": "奶油白",
                "sku": "HUMIDIFIER-WHITE",
                "price_cents": 8900,
                "stock": 22,
            }
        ],
    },
    {
        "category_slug": "desktop-appliances",
        "name": "折叠桌面风扇",
        "slug": "folding-desk-fan",
        "summary": "多档风速，可折叠收纳。",
        "description": "USB 充电折叠桌面风扇，适合办公室与床头使用。",
        "variants": [
            {
                "name": "白色",
                "sku": "FAN-FOLD-WHITE",
                "price_cents": 9900,
                "stock": 30,
            },
            {
                "name": "雾绿色",
                "sku": "FAN-FOLD-GREEN",
                "price_cents": 9900,
                "stock": 16,
            },
        ],
    },
    {
        "category_slug": "office-stationery",
        "name": "A5 硬壳笔记本",
        "slug": "a5-hardcover-notebook",
        "summary": "可平摊装订，适合会议和日常记录。",
        "description": "120 页 A5 横线硬壳笔记本，纸张顺滑不透墨。",
        "variants": [
            {
                "name": "米白色",
                "sku": "NOTEBOOK-A5-BEIGE",
                "price_cents": 3900,
                "stock": 80,
            }
        ],
    },
    {
        "category_slug": "office-stationery",
        "name": "桌面收纳盒",
        "slug": "desktop-organizer",
        "summary": "分区收纳文具与数码小物。",
        "description": "多格桌面收纳盒，整理笔、便签和充电配件。",
        "variants": [
            {
                "name": "暖白色",
                "sku": "ORGANIZER-WHITE",
                "price_cents": 4900,
                "stock": 42,
            }
        ],
    },
]


def seed_database(session: Session) -> None:
    categories: dict[str, Category] = {}

    for seed in CATEGORY_SEEDS:
        category = session.scalar(
            select(Category).where(Category.slug == seed["slug"])
        )
        if category is None:
            category = Category(**seed)
            session.add(category)
            session.flush()
        categories[seed["slug"]] = category

    for seed in PRODUCT_SEEDS:
        product = session.scalar(
            select(Product).where(Product.slug == seed["slug"])
        )
        if product is not None:
            continue

        product = Product(
            category_id=categories[seed["category_slug"]].id,
            name=seed["name"],
            slug=seed["slug"],
            summary=seed["summary"],
            description=seed["description"],
        )
        session.add(product)
        session.flush()

        for variant_seed in seed["variants"]:
            session.add(ProductVariant(product_id=product.id, **variant_seed))

        session.add(
            ProductImage(
                product_id=product.id,
                url="/product-placeholder.svg",
                alt=f"{seed['name']}商品图",
            )
        )

    session.commit()


if __name__ == "__main__":
    with SessionLocal() as db_session:
        seed_database(db_session)
        print("Seeded product catalog.")

