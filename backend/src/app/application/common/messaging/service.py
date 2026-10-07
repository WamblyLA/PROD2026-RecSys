from typing import Protocol

from app.application.chat.dto import ChatMessageItem
from app.domain.user.entity import UserId


class MessageConsumer(Protocol):
    async def deliver(self, message: ChatMessageItem) -> None: ...


class MessagingService(Protocol):
    async def publish(self, for_user: UserId, message: ChatMessageItem) -> None: ...

    def register(self, user_id: UserId, consumer: MessageConsumer) -> None: ...

    def unregister(self, user_id: UserId, consumer: MessageConsumer) -> None: ...
