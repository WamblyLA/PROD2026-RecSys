from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.chat.data_gateway import ChatDataGateway
from app.domain.chat.entity import Chat, ChatId, Message, MessageId, normalize_pair
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.tables import chat_table, message_table


class DefaultChatDataGateway(ChatDataGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def load_by_users(self, user_id_1: UserId, user_id_2: UserId) -> Chat | None:
        user_a_id, user_b_id = normalize_pair(user_id_1, user_id_2)

        stmt = (
            select(chat_table)
            .where(chat_table.c.user_a_id == user_a_id)
            .where(chat_table.c.user_b_id == user_b_id)
            .where(chat_table.c.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return Chat(
            id=ChatId(row.id),
            user_a_id=row.user_a_id,
            user_b_id=row.user_b_id,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )

    @override
    async def load_chat_by_id(self, chat_id: ChatId) -> Chat | None:
        stmt = select(chat_table).where(chat_table.c.id == chat_id).where(chat_table.c.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return Chat(
            id=ChatId(row.id),
            user_a_id=row.user_a_id,
            user_b_id=row.user_b_id,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )

    @override
    async def list_chats_for_user(self, user_id: UserId) -> list[Chat]:
        stmt = (
            select(chat_table)
            .where(chat_table.c.deleted_at.is_(None))
            .where(
                (chat_table.c.user_a_id == user_id) | (chat_table.c.user_b_id == user_id),
            )
            .order_by(chat_table.c.created_at.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return [
            Chat(
                id=ChatId(row.id),
                user_a_id=row.user_a_id,
                user_b_id=row.user_b_id,
                created_at=row.created_at,
                deleted_at=row.deleted_at,
            )
            for row in rows
        ]

    @override
    async def list_messages(
        self,
        chat_id: ChatId,
        *,
        limit: int,
        before_message_id: MessageId | None = None,
    ) -> list[Message]:
        stmt = (
            select(message_table).where(message_table.c.chat_id == chat_id).where(message_table.c.deleted_at.is_(None))
        )
        if before_message_id is not None:
            stmt = stmt.where(message_table.c.id < before_message_id)
        stmt = stmt.order_by(message_table.c.created_at.desc()).limit(limit)

        result = await self._session.execute(stmt)
        rows = result.fetchall()
        messages = [
            Message(
                id=MessageId(row.id),
                chat_id=ChatId(row.chat_id),
                sender_user_id=row.sender_user_id,
                text=row.text,
                created_at=row.created_at,
                deleted_at=row.deleted_at,
            )
            for row in rows
        ]
        messages.reverse()
        return messages
