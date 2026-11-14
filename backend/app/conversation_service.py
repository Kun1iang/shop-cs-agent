from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.llm import DeepSeekClient
from app.models import (
    Conversation,
    ConversationMessage,
    Product,
    User,
)
from app.order_service import list_orders
from app.prompts import CUSTOMER_SERVICE_SYSTEM_PROMPT
from app.schemas import ConversationDetail, PageContext


class ConversationNotFoundError(Exception):
    pass


def conversation_load_options():
    return (selectinload(Conversation.messages),)


def get_or_create_conversation(
    db: Session,
    user_id: int,
    client_type: str = "web",
) -> Conversation:
    conversation = Conversation(
        id=str(uuid4()),
        user_id=user_id,
        client_type=client_type,
    )
    db.add(conversation)
    db.commit()
    return conversation


def get_conversation(
    db: Session,
    user_id: int,
    conversation_id: str,
) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .options(*conversation_load_options())
        .execution_options(populate_existing=True)
    )
    if conversation is None:
        raise ConversationNotFoundError("会话不存在")
    return conversation


def conversation_detail(conversation: Conversation) -> ConversationDetail:
    return ConversationDetail(
        id=conversation.id,
        client_type=conversation.client_type,
        messages=conversation.messages,
    )


def build_fact_context(
    db: Session,
    user: User,
    page_context: PageContext,
) -> str:
    facts = [
        f"当前用户：{user.display_name}（user_id={user.id}）",
        "商城范围：数码配件、桌面小电器、办公文具。",
        "支付与退款：当前为模拟流程。",
    ]

    orders = list_orders(db, user.id)[:5]
    if orders:
        order_lines = []
        for order in orders:
            products = "、".join(
                f"{item.product_name}×{item.quantity}"
                for item in order.items
            )
            order_lines.append(
                f"{order.order_no}：{order.status}，{products}，"
                f"总额 {order.total_cents / 100:.2f} 元"
            )
        facts.append("最近订单：\n" + "\n".join(order_lines))
    else:
        facts.append("当前用户暂无订单。")

    if page_context.product_slug:
        product = db.scalar(
            select(Product)
            .where(
                Product.slug == page_context.product_slug,
                Product.status == "active",
            )
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
            )
        )
        if product:
            variants = "；".join(
                f"{variant.name} {variant.price_cents / 100:.2f} 元，"
                f"库存 {variant.stock}"
                for variant in product.variants
                if variant.is_active
            )
            facts.append(
                f"用户当前查看商品：{product.name}，"
                f"分类 {product.category.name}，{product.summary}；"
                f"规格：{variants}"
            )

    if page_context.order_no:
        matching_order = next(
            (
                order
                for order in orders
                if order.order_no == page_context.order_no
            ),
            None,
        )
        if matching_order:
            facts.append(
                f"用户当前查看订单：{matching_order.order_no}，"
                f"状态 {matching_order.status}，"
                f"总额 {matching_order.total_cents / 100:.2f} 元"
            )

    return "\n\n".join(facts)


def send_message(
    db: Session,
    user: User,
    conversation_id: str,
    message: str,
    page_context: PageContext,
    llm_client: DeepSeekClient,
) -> tuple[str, list[ConversationMessage]]:
    conversation = get_conversation(db, user.id, conversation_id)
    history = conversation.messages[-10:]
    llm_messages = [
        {"role": item.role, "content": item.content}
        for item in history
        if item.role in {"user", "assistant"}
    ]
    llm_messages.append({"role": "user", "content": message})

    facts = build_fact_context(db, user, page_context)
    system_prompt = (
        f"{CUSTOMER_SERVICE_SYSTEM_PROMPT}\n\n"
        f"系统提供的可信用事实：\n{facts}"
    )
    reply = llm_client.reply(system_prompt, llm_messages)

    user_message = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply,
    )
    conversation.updated_at = datetime.now(UTC)
    db.add_all([user_message, assistant_message])
    db.commit()

    updated = get_conversation(db, user.id, conversation.id)
    return reply, updated.messages

