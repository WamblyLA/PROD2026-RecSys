from dataclasses import dataclass

from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.notification_device.data_gateway import NotificationDeviceDataGateway
from app.domain.notification_device.entity import NotificationDevice


@dataclass(frozen=True, slots=True)
class RegisterNotificationDeviceRequest:
    device_id: str


@interactor
class RegisterNotificationDeviceInteractor:
    identity_provider: IdentityProvider
    notification_device_data_gateway: NotificationDeviceDataGateway
    unit_of_work: UnitOfWork

    async def execute(self, request: RegisterNotificationDeviceRequest) -> None:
        current_user = await self.identity_provider.get_current_user()

        # Один и тот же physical-девайс (device_id) должен быть привязан только к одному аккаунту.
        # Перед регистрацией удаляем все старые записи с этим токеном.
        await self.notification_device_data_gateway.delete_by_device_id(request.device_id)

        existing_device = await self.notification_device_data_gateway.load_by_user_id_and_device_id(
            user_id=current_user.id,
            device_id=request.device_id,
        )

        if existing_device:
            return

        notification_device = NotificationDevice.factory(
            user_id=current_user.id,
            device_id=request.device_id,
        )

        await self.unit_of_work.add(notification_device)
        await self.unit_of_work.commit()
