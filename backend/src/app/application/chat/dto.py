from datetime import datetime

from app.application.common.dto import dto
from app.application.profile.dto import SelfCardResult
from app.domain.chat.entity import ChatId, MessageId
from app.domain.user.entity import UserId


@dto
class ChatItemResult:
    chat_id: ChatId
    other_user_id: UserId
    last_message_id: MessageId | None
    last_message_text: str | None
    last_message_created_at: datetime | None
    other_user_card: SelfCardResult | None


@dto
class ChatListResult:
    items: list[ChatItemResult]


@dto
class ChatMessageItem:
    message_id: MessageId
    chat_id: ChatId
    sender_user_id: UserId
    text: str
    created_at: datetime


@dto
class ChatMessagesResult:
    items: list[ChatMessageItem]
