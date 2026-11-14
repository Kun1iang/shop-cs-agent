import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import cart_service
from app.knowledge_base import knowledge_base
from app.llm import DeepSeekClient, LLMResponseError
from app.models import HandoffTicket, Product, ToolCall, User
from app.order_service import list_orders
from app.prompts import CUSTOMER_SERVICE_SYSTEM_PROMPT
from app.schemas import PageContext

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_orders",
            "description": "查询当前用户最近的订单列表。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "按订单号查询当前用户的一笔订单，只能访问当前用户自己的订单。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_no": {"type": "string"},
                },
                "required": ["order_no"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "按商品 slug 查询商品、价格、规格和库存事实。",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                },
                "required": ["slug"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart",
            "description": "查询当前用户购物车中的商品、数量和金额。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "检索售后政策、退款、发票、发货和转人工规则。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "handoff_to_human",
            "description": "创建转人工工单。用户明确要求人工，或问题无法安全处理时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "转人工原因",
                    }
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
]


@dataclass
class AgentResult:
    reply: str
    tool_call_count: int
    handoff_ticket_no: str | None = None


def order_to_dict(order) -> dict:
    return {
        "order_no": order.order_no,
        "status": order.status,
        "subtotal_cents": order.subtotal_cents,
        "total_cents": order.total_cents,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "product_name": item.product_name,
                "variant_name": item.variant_name,
                "sku": item.sku,
                "unit_price_cents": item.unit_price_cents,
                "quantity": item.quantity,
                "line_total_cents": item.line_total_cents,
            }
            for item in order.items
        ],
    }


class SupportToolExecutor:
    def __init__(
        self,
        db: Session,
        user: User,
        conversation_id: str,
    ) -> None:
        self.db = db
        self.user = user
        self.conversation_id = conversation_id
        self.handoff_ticket_no: str | None = None

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        status = "success"
        try:
            result = self._dispatch(name, arguments)
        except Exception as error:  # noqa: BLE001 - tool boundary isolates failures
            status = "error"
            result = {"error": str(error)}

        result_json = json.dumps(result, ensure_ascii=False)
        self.db.add(
            ToolCall(
                conversation_id=self.conversation_id,
                name=name,
                arguments_json=json.dumps(arguments, ensure_ascii=False),
                result_json=result_json,
                status=status,
            )
        )
        self.db.commit()
        return result_json

    def _dispatch(self, name: str, arguments: dict[str, Any]) -> dict | list:
        if name == "get_my_orders":
            return [
                order_to_dict(order)
                for order in list_orders(self.db, self.user.id)[:5]
            ]

        if name == "get_order":
            order_no = str(arguments["order_no"])
            order = next(
                (
                    item
                    for item in list_orders(self.db, self.user.id)
                    if item.order_no == order_no
                ),
                None,
            )
            if order is None:
                raise ValueError("订单不存在或不属于当前用户")
            return order_to_dict(order)

        if name == "get_product":
            slug = str(arguments["slug"])
            product = self.db.scalar(
                select(Product)
                .where(Product.slug == slug, Product.status == "active")
                .options(
                    selectinload(Product.category),
                    selectinload(Product.variants),
                )
            )
            if product is None:
                raise ValueError("商品不存在或已下架")
            return {
                "name": product.name,
                "slug": product.slug,
                "summary": product.summary,
                "description": product.description,
                "category": product.category.name,
                "variants": [
                    {
                        "name": variant.name,
                        "sku": variant.sku,
                        "price_cents": variant.price_cents,
                        "stock": variant.stock,
                    }
                    for variant in product.variants
                    if variant.is_active
                ],
            }

        if name == "get_cart":
            cart = cart_service.get_or_create_cart(self.db, self.user.id)
            return cart_service.cart_to_summary(cart).model_dump()

        if name == "search_policy":
            results = knowledge_base.search(str(arguments["query"]))
            return [
                {
                    "source": result.source,
                    "title": result.title,
                    "content": result.content,
                }
                for result in results
            ]

        if name == "handoff_to_human":
            reason = str(arguments["reason"]).strip() or "用户需要人工协助"
            ticket_no = (
                f"HO{datetime.now(UTC):%Y%m%d%H%M%S}"
                f"{uuid4().hex[:6].upper()}"
            )
            self.db.add(
                HandoffTicket(
                    ticket_no=ticket_no,
                    user_id=self.user.id,
                    conversation_id=self.conversation_id,
                    reason=reason,
                )
            )
            self.handoff_ticket_no = ticket_no
            return {
                "ticket_no": ticket_no,
                "status": "open",
                "reason": reason,
            }

        raise ValueError(f"未知工具：{name}")


def _tool_call_payload(tool_call) -> dict:
    return {
        "id": tool_call.id,
        "type": "function",
        "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
        },
    }


def run_support_agent(
    db: Session,
    user: User,
    conversation_id: str,
    history: list[dict[str, str]],
    message: str,
    page_context: PageContext,
    llm_client: DeepSeekClient,
    max_tool_rounds: int = 4,
) -> AgentResult:
    context_hints = [
        f"当前用户：{user.display_name}（user_id={user.id}）",
        f"当前页面：{page_context.page or 'unknown'}",
    ]
    if page_context.product_slug:
        context_hints.append(f"当前商品 slug：{page_context.product_slug}")
    if page_context.order_no:
        context_hints.append(f"当前订单号：{page_context.order_no}")
    context_hints.append(
        "商品、购物车、订单和政策事实必须通过工具查询，不能凭上下文猜测。"
    )

    system_prompt = (
        f"{CUSTOMER_SERVICE_SYSTEM_PROMPT}\n\n"
        "页面上下文提示：\n" + "\n".join(context_hints)
    )
    messages: list[dict[str, Any]] = [
        *history,
        {"role": "user", "content": message},
    ]
    executor = SupportToolExecutor(db, user, conversation_id)
    tool_call_count = 0

    for _ in range(max_tool_rounds):
        response = llm_client.complete(
            system_prompt,
            messages,
            TOOL_DEFINITIONS,
        )
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            content = getattr(response, "content", None)
            if not content or not content.strip():
                raise LLMResponseError("模型没有返回有效内容")
            return AgentResult(
                reply=content.strip(),
                tool_call_count=tool_call_count,
                handoff_ticket_no=executor.handoff_ticket_no,
            )

        messages.append(
            {
                "role": "assistant",
                "content": getattr(response, "content", None),
                "tool_calls": [
                    _tool_call_payload(tool_call) for tool_call in tool_calls
                ],
            }
        )
        for tool_call in tool_calls:
            tool_call_count += 1
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = executor.execute(tool_call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    raise LLMResponseError("工具调用轮次超过上限")
