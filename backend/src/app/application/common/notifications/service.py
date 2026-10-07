from abc import abstractmethod
from enum import StrEnum
from typing import Protocol


class NotificationType(StrEnum):
    LIKE = "LIKE"
    MATCH = "MATCH"
    MESSAGE = "MESSAGE"
    GENERIC = "GENERIC"


class NotificationService(Protocol):
    @abstractmethod
    async def send_notification(
        self,
        identifier: str,
        title: str,
        body: str,
        notification_type: NotificationType,
        data: dict[str, str] | None = None,
    ) -> None:
        raise NotImplementedError
