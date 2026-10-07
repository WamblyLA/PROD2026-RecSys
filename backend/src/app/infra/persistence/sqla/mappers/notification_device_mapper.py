from app.domain.notification_device.entity import NotificationDevice, NotificationDeviceId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import NotificationDeviceRow


class NotificationDeviceMapper:
    entity_type: type[NotificationDevice] = NotificationDevice

    @staticmethod
    def to_rows(device: NotificationDevice) -> list[NotificationDeviceRow]:
        return [
            NotificationDeviceRow(
                id_=device.id,
                user_id=device.user_id,
                device_id=device.device_id,
                deleted_at=device.deleted_at,
                created_at=device.created_at,
            ),
        ]

    @staticmethod
    def to_entity(row: NotificationDeviceRow) -> NotificationDevice:
        if row.id is None or row.user_id is None or row.device_id is None or row.created_at is None:
            msg = "NotificationDeviceRow must have id, user_id, device_id, created_at"
            raise ValueError(msg)
        return NotificationDevice(
            id=NotificationDeviceId(row.id),
            user_id=UserId(row.user_id),
            device_id=row.device_id,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
        )
