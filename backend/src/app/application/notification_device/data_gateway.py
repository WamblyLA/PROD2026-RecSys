from abc import abstractmethod
from typing import Protocol

from app.domain.notification_device.entity import NotificationDevice
from app.domain.user.entity import UserId


class NotificationDeviceDataGateway(Protocol):
    @abstractmethod
    async def load_by_user_id(self, user_id: UserId) -> NotificationDevice | None:
        raise NotImplementedError

    @abstractmethod
    async def load_by_user_id_and_device_id(
        self,
        user_id: UserId,
        device_id: str,
    ) -> NotificationDevice | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_device_id(self, device_id: str) -> None:
        raise NotImplementedError
