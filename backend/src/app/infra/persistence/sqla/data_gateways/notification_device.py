from typing import override

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.notification_device.data_gateway import NotificationDeviceDataGateway
from app.domain.notification_device.entity import NotificationDevice
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.mappers.notification_device_mapper import NotificationDeviceMapper
from app.infra.persistence.sqla.rows import NotificationDeviceRow
from app.infra.persistence.sqla.tables import notification_device_table


class DefaultNotificationDeviceDataGateway(NotificationDeviceDataGateway):
    def __init__(self, session: AsyncSession, notification_device_mapper: NotificationDeviceMapper) -> None:
        self._session = session
        self._notification_device_mapper = notification_device_mapper

    @override
    async def load_by_user_id(self, user_id: UserId) -> NotificationDevice | None:
        statement = select(NotificationDeviceRow).where(
            notification_device_table.c.user_id == user_id,
        )
        result = await self._session.execute(statement)
        row = result.scalar_one_or_none()
        return self._notification_device_mapper.to_entity(row) if row is not None else None

    @override
    async def load_by_user_id_and_device_id(
        self,
        user_id: UserId,
        device_id: str,
    ) -> NotificationDevice | None:
        statement = select(NotificationDeviceRow).where(
            notification_device_table.c.user_id == user_id,
            notification_device_table.c.device_id == device_id,
        )
        result = await self._session.execute(statement)
        row = result.scalar_one_or_none()
        return self._notification_device_mapper.to_entity(row) if row is not None else None

    @override
    async def delete_by_device_id(self, device_id: str) -> None:
        statement = delete(notification_device_table).where(notification_device_table.c.device_id == device_id)
        await self._session.execute(statement)
