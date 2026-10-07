from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.presentation.api.routes.profile.dto import (
    SelfCardResponse,
)


class ChatItemResponse(BaseModel):
    chat_id: UUID
    other_user_id: UUID
    last_message_id: UUID | None
    last_message_text: str | None
    last_message_created_at: datetime | None
    other_user_card: SelfCardResponse | None


class ChatsResponse(BaseModel):
    items: list[ChatItemResponse]


class ChatMessageItemResponse(BaseModel):
    message_id: UUID
    chat_id: UUID
    sender_user_id: UUID
    text: str
    created_at: datetime


class ChatMessagesResponse(BaseModel):
    items: list[ChatMessageItemResponse]


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
