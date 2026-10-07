from dataclasses import dataclass

from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.notifications.service import NotificationService, NotificationType
from app.application.notification_device.data_gateway import NotificationDeviceDataGateway
from app.application.notification_device.errors import NotificationDeviceNotFoundError


@dataclass(frozen=True, slots=True)
class SendNotificationRequest:
    title: str
    body: str
    data: dict[str, str] | None = None


@interactor
class SendNotificationInteractor:
    identity_provider: IdentityProvider
    notification_device_data_gateway: NotificationDeviceDataGateway
    notification_service: NotificationService

    async def execute(self, request: SendNotificationRequest) -> None:
        current_user = await self.identity_provider.get_current_user()
        notification_device = await self.notification_device_data_gateway.load_by_user_id(current_user.id)

        if not notification_device:
            raise NotificationDeviceNotFoundError

        await self.notification_service.send_notification(
            identifier=notification_device.device_id,
            title=request.title,
            body=request.body,
            notification_type=NotificationType.GENERIC,
            data=request.data,
        )
