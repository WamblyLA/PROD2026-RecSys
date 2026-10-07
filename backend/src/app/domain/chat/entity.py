from datetime import UTC, datetime
from typing import NewType, Self
from uuid import UUID

from uuid_utils.compat import uuid7

from app.domain.common.entity import Entity, entity
from app.domain.user.entity import UserId

ChatId = NewType("ChatId", UUID)
MessageId = NewType("MessageId", UUID)


def normalize_pair(user_id_1: UserId, user_id_2: UserId) -> tuple[UserId, UserId]:
    if user_id_1 <= user_id_2:
        return user_id_1, user_id_2
    return user_id_2, user_id_1


@entity
class Chat(Entity[ChatId]):
    user_a_id: UserId
    user_b_id: UserId

    @classmethod
    def factory(cls, user_id_1: UserId, user_id_2: UserId) -> Self:
        user_a_id, user_b_id = normalize_pair(user_id_1, user_id_2)
        return cls(
            id=ChatId(uuid7()),
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            created_at=datetime.now(tz=UTC),
        )


@entity
class Message(Entity[MessageId]):
    chat_id: ChatId
    sender_user_id: UserId
    text: str

    @classmethod
    def factory(cls, chat_id: ChatId, sender_user_id: UserId, text: str) -> Self:
        return cls(
            id=MessageId(uuid7()),
            chat_id=chat_id,
            sender_user_id=sender_user_id,
            text=text,
            created_at=datetime.now(tz=UTC),
        )
