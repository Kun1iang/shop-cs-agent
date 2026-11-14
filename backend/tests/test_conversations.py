from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm import get_llm_client
from app.main import app
from app.models import ToolCall


class FakeLLM:
    def __init__(self) -> None:
        self.last_system_prompt = ""
        self.last_messages: list[dict[str, str]] = []

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> SimpleNamespace:
        self.last_system_prompt = system_prompt
        self.last_messages = messages
        return SimpleNamespace(
            content="我看到了你的订单信息，这是一笔模拟支付订单。",
            tool_calls=None,
        )


def test_conversation_persists_messages(client: TestClient) -> None:
    fake_llm = FakeLLM()
    app.dependency_overrides[get_llm_client] = lambda: fake_llm

    created = client.post("/api/v1/conversations")
    assert created.status_code == 200
    conversation_id = created.json()["conversation_id"]

    sent = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "message": "我的订单现在是什么状态？",
            "page_context": {"page": "orders"},
        },
    )

    assert sent.status_code == 200
    assert sent.json()["reply"] == "我看到了你的订单信息，这是一笔模拟支付订单。"
    assert [message["role"] for message in sent.json()["messages"]] == [
        "user",
        "assistant",
    ]

    loaded = client.get(f"/api/v1/conversations/{conversation_id}")
    assert loaded.status_code == 200
    assert len(loaded.json()["messages"]) == 2
    app.dependency_overrides.pop(get_llm_client, None)


class FakeToolCallingLLM:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no
        self.calls = 0

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> SimpleNamespace:
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(
                content=None,
                tool_calls=[
                    SimpleNamespace(
                        id="call-order-1",
                        function=SimpleNamespace(
                            name="get_order",
                            arguments=f'{{"order_no": "{self.order_no}"}}',
                        ),
                    )
                ],
            )
        tool_message = next(
            message for message in reversed(messages) if message["role"] == "tool"
        )
        assert self.order_no in tool_message["content"]
        return SimpleNamespace(
            content="工具返回了你的订单，状态是已支付。",
            tool_calls=None,
        )


def test_agent_executes_tool_and_audits_call(
    client: TestClient,
    db_session: Session,
) -> None:
    product = client.get("/api/v1/products/a5-hardcover-notebook").json()
    variant_id = product["variants"][0]["id"]
    client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 1},
    )
    order = client.post(
        "/api/v1/orders/checkout",
        headers={"Idempotency-Key": uuid4().hex},
    ).json()

    fake_llm = FakeToolCallingLLM(order["order_no"])
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    conversation_id = client.post("/api/v1/conversations").json()[
        "conversation_id"
    ]

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "message": "帮我查这个订单",
            "page_context": {
                "page": "order_detail",
                "order_no": order["order_no"],
            },
        },
    )

    assert response.status_code == 200
    assert "已支付" in response.json()["reply"]
    assert fake_llm.calls == 2

    db_session.expire_all()
    audit = db_session.scalar(select(ToolCall))
    assert audit is not None
    assert audit.name == "get_order"
    assert audit.status == "success"
    assert order["order_no"] in audit.result_json

    app.dependency_overrides.pop(get_llm_client, None)


def test_chat_context_contains_current_user_order(client: TestClient) -> None:
    fake_llm = FakeLLM()
    app.dependency_overrides[get_llm_client] = lambda: fake_llm

    product = client.get("/api/v1/products/a5-hardcover-notebook").json()
    variant_id = product["variants"][0]["id"]
    client.post(
        "/api/v1/cart/items",
        json={"variant_id": variant_id, "quantity": 1},
    )
    order = client.post(
        "/api/v1/orders/checkout",
        headers={"Idempotency-Key": uuid4().hex},
    ).json()

    conversation_id = client.post("/api/v1/conversations").json()[
        "conversation_id"
    ]
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "message": "帮我看看这笔订单",
            "page_context": {
                "page": "order_detail",
                "order_no": order["order_no"],
            },
        },
    )

    assert response.status_code == 200
    assert order["order_no"] in fake_llm.last_system_prompt
    assert fake_llm.last_messages[-1]["content"] == "帮我看看这笔订单"

    app.dependency_overrides.pop(get_llm_client, None)


def test_chat_rejects_unknown_conversation(client: TestClient) -> None:
    fake_llm = FakeLLM()
    app.dependency_overrides[get_llm_client] = lambda: fake_llm

    response = client.post(
        "/api/v1/conversations/not-found/messages",
        json={"message": "你好", "page_context": {}},
    )

    assert response.status_code == 404
    app.dependency_overrides.pop(get_llm_client, None)
