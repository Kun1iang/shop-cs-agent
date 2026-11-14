from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import agent_service
from app.llm import DeepSeekClient
from app.models import Conversation, ConversationMessage, User
from app.schemas import ConversationDetail, HandoffInfo, PageContext


class ConversationResult:
    def __init__(
        self,
        reply: str,
        messages: list[ConversationMessage],
        tool_call_count: int,
        handoff: HandoffInfo | None,
    ) -> None:
        self.reply = reply
        self.messages = messages
        self.tool_call_count = tool_call_count
        self.handoff = handoff


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


def send_message(
    db: Session,
    user: User,
    conversation_id: str,
    message: str,
    page_context: PageContext,
    llm_client: DeepSeekClient,
) -> ConversationResult:
    conversation = get_conversation(db, user.id, conversation_id)
    history = conversation.messages[-10:]
    llm_messages = [
        {"role": item.role, "content": item.content}
        for item in history
        if item.role in {"user", "assistant"}
    ]
    result = agent_service.run_support_agent(
        db,
        user,
        conversation.id,
        llm_messages,
        message,
        page_context,
        llm_client,
    )
    reply = result.reply
    handoff = (
        HandoffInfo(
            ticket_no=result.handoff_ticket_no,
            status="open",
            reason="已创建转人工工单",
        )
        if result.handoff_ticket_no
        else None
    )

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
    return ConversationResult(
        reply=reply,
        messages=updated.messages,
        tool_call_count=result.tool_call_count,
        handoff=handoff,
    )

