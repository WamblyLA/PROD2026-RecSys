from datetime import UTC, datetime
from typing import NewType, Self
from uuid import UUID

from uuid_utils.compat import uuid7

from app.domain.common.entity import Entity, entity
from app.domain.user.entity import UserId

NotificationDeviceId = NewType("NotificationDeviceId", UUID)


@entity
class NotificationDevice(Entity[NotificationDeviceId]):
    user_id: UserId
    device_id: str

    @classmethod
    def factory(cls, user_id: UserId, device_id: str) -> Self:
        return cls(
            id=NotificationDeviceId(uuid7()),
            user_id=user_id,
            device_id=device_id,
            created_at=datetime.now(tz=UTC),
        )
