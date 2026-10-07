from abc import abstractmethod
from typing import Protocol

from app.domain.chat.entity import Chat, ChatId, Message, MessageId
from app.domain.user.entity import UserId


class ChatDataGateway(Protocol):
    @abstractmethod
    async def load_by_users(self, user_id_1: UserId, user_id_2: UserId) -> Chat | None:
        """Return existing 1:1 chat for user pair, if any."""
        raise NotImplementedError

    @abstractmethod
    async def load_chat_by_id(self, chat_id: ChatId) -> Chat | None:
        raise NotImplementedError

    @abstractmethod
    async def list_chats_for_user(self, user_id: UserId) -> list[Chat]:
        raise NotImplementedError

    @abstractmethod
    async def list_messages(
        self,
        chat_id: ChatId,
        *,
        limit: int,
        before_message_id: MessageId | None = None,
    ) -> list[Message]:
        raise NotImplementedError
