import asyncio
from collections import defaultdict
from typing import override

import structlog

from app.application.chat.dto import ChatMessageItem
from app.application.common.messaging.service import MessageConsumer, MessagingService
from app.domain.user.entity import UserId

logger = structlog.get_logger(__name__)


class InMemoryMessagingService(MessagingService):
    def __init__(self) -> None:
        self._consumers: defaultdict[UserId, set[MessageConsumer]] = defaultdict(set)
        self._lock = asyncio.Lock()

    @override
    async def publish(self, for_user: UserId, message: ChatMessageItem) -> None:
        async with self._lock:
            consumers = list(self._consumers.get(for_user, set()))

        for consumer in consumers:
            try:
                await consumer.deliver(message)
            except Exception:  # noqa: BLE001
                # На ошибках доставки просто отписываем консьюмера.
                logger.info("delivery error, unregistering user", user_id=for_user)
                await self._unregister_safely(for_user, consumer)

    @override
    def register(self, user_id: UserId, consumer: MessageConsumer) -> None:
        self._consumers[user_id].add(consumer)

    @override
    def unregister(self, user_id: UserId, consumer: MessageConsumer) -> None:
        if user_id not in self._consumers:
            return
        self._consumers[user_id].discard(consumer)
        if not self._consumers[user_id]:
            del self._consumers[user_id]

    async def _unregister_safely(self, user_id: UserId, consumer: MessageConsumer) -> None:
        async with self._lock:
            self.unregister(user_id, consumer)
