from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.notification_device.interactors.register_device import RegisterNotificationDeviceInteractor
from app.application.notification_device.interactors.send_notification import SendNotificationInteractor


class NotificationDeviceInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[RegisterNotificationDeviceInteractor],
        WithParents[SendNotificationInteractor],
    )


providers = [
    NotificationDeviceInteractorProvider(),
]
