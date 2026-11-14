import json
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app import conversation_service
from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.llm import (
    DeepSeekClient,
    LLMResponseError,
    LLMUnavailableError,
    get_llm_client,
)
from app.schemas import (
    ChatMessageOut,
    ConversationCreated,
    ConversationDetail,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
LLMClient = Annotated[DeepSeekClient, Depends(get_llm_client)]


def map_conversation_error(error: Exception) -> HTTPException:
    if isinstance(error, conversation_service.ConversationNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, LLMUnavailableError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        )
    if isinstance(error, LLMResponseError):
        return HTTPException(status_code=502, detail=str(error))
    return HTTPException(status_code=502, detail="客服服务暂时不可用")


@router.post("", response_model=ConversationCreated)
def create_conversation(user: CurrentUser, db: DbSession) -> ConversationCreated:
    conversation = conversation_service.get_or_create_conversation(
        db,
        user.id,
    )
    return ConversationCreated(conversation_id=conversation.id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def read_conversation(
    conversation_id: str,
    user: CurrentUser,
    db: DbSession,
) -> ConversationDetail:
    try:
        conversation = conversation_service.get_conversation(
            db,
            user.id,
            conversation_id,
        )
    except Exception as error:
        raise map_conversation_error(error) from error
    return conversation_service.conversation_detail(conversation)


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
def send_chat_message(
    conversation_id: str,
    payload: SendMessageRequest,
    user: CurrentUser,
    db: DbSession,
    llm_client: LLMClient,
) -> SendMessageResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="消息不能超过 2000 字")

    try:
        result = conversation_service.send_message(
            db,
            user,
            conversation_id,
            message,
            payload.page_context,
            llm_client,
        )
    except Exception as error:
        raise map_conversation_error(error) from error

    return SendMessageResponse(
        conversation_id=conversation_id,
        reply=result.reply,
        messages=result.messages,
        tool_call_count=result.tool_call_count,
        handoff=result.handoff,
    )


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/{conversation_id}/messages/stream")
def stream_chat_message(
    conversation_id: str,
    payload: SendMessageRequest,
    user: CurrentUser,
    db: DbSession,
    llm_client: LLMClient,
) -> StreamingResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="消息不能超过 2000 字")

    def generate():
        try:
            result = conversation_service.send_message(
                db,
                user,
                conversation_id,
                message,
                payload.page_context,
                llm_client,
            )
            yield sse_event(
                "meta",
                {
                    "conversation_id": conversation_id,
                    "tool_call_count": result.tool_call_count,
                    "handoff": (
                        result.handoff.model_dump()
                        if result.handoff
                        else None
                    ),
                },
            )

            chunk_size = settings.stream_chunk_size
            for start in range(0, len(result.reply), chunk_size):
                yield sse_event(
                    "token",
                    {"text": result.reply[start : start + chunk_size]},
                )
                if settings.stream_token_delay_seconds > 0:
                    time.sleep(settings.stream_token_delay_seconds)

            serialized_messages = [
                ChatMessageOut.model_validate(item).model_dump(mode="json")
                for item in result.messages
            ]
            yield sse_event(
                "done",
                {
                    "conversation_id": conversation_id,
                    "messages": serialized_messages,
                },
            )
        except Exception as error:  # noqa: BLE001 - must become an SSE error event
            detail = map_conversation_error(error).detail
            yield sse_event("error", {"detail": detail})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

