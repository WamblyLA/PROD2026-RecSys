from dishka import BaseScope, Provider, Scope, provide

from app.application.common.notifications.service import NotificationService
from app.infra.notifications.fcm import FCMNotificationService


class NotificationServiceProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide
    def notification_service(self) -> NotificationService:
        return FCMNotificationService()


providers = [
    NotificationServiceProvider(),
]
