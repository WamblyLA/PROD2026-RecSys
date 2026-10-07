from collections.abc import Iterable

from app.domain.chat.entity import Chat, ChatId, Message, MessageId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.mappers.errors import MapperNotFoundError
from app.infra.persistence.sqla.rows import ChatRow, MessageRow


class ChatMapper:
    entity_type = Chat

    def to_rows(self, entity: Chat) -> Iterable[ChatRow]:
        if not isinstance(entity, Chat):
            raise MapperNotFoundError(type(entity))
        row = ChatRow()
        row.id = entity.id
        row.user_a_id = entity.user_a_id
        row.user_b_id = entity.user_b_id
        row.created_at = entity.created_at
        row.deleted_at = entity.deleted_at
        return [row]

    def to_entity(self, row: ChatRow) -> Chat:
        return Chat(
            id=ChatId(row.id),
            user_a_id=UserId(row.user_a_id),
            user_b_id=UserId(row.user_b_id),
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )


class MessageMapper:
    entity_type = Message

    def to_rows(self, entity: Message) -> Iterable[MessageRow]:
        if not isinstance(entity, Message):
            raise MapperNotFoundError(type(entity))
        row = MessageRow()
        row.id = entity.id
        row.chat_id = entity.chat_id
        row.sender_user_id = entity.sender_user_id
        row.text = entity.text
        row.created_at = entity.created_at
        row.deleted_at = entity.deleted_at
        return [row]

    def to_entity(self, row: MessageRow) -> Message:
        return Message(
            id=MessageId(row.id),
            chat_id=ChatId(row.chat_id),
            sender_user_id=UserId(row.sender_user_id),
            text=row.text,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )
