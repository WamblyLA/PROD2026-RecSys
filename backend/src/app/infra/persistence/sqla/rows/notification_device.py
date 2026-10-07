from datetime import datetime
from uuid import UUID


class NotificationDeviceRow:
    id: UUID | None
    user_id: UUID | None
    device_id: str | None
    deleted_at: datetime | None
    created_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        user_id: UUID | None = None,
        device_id: str | None = None,
        deleted_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.user_id = user_id
        self.device_id = device_id
        self.deleted_at = deleted_at
        self.created_at = created_at
