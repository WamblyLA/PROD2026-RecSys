import asyncio
from typing import override

from firebase_admin import messaging
from firebase_admin.messaging import Message, Notification
from structlog import get_logger

from app.application.common.notifications.service import NotificationService, NotificationType

logger = get_logger(__name__)


class FCMNotificationService(NotificationService):
    @override
    async def send_notification(
        self,
        identifier: str,
        title: str,
        body: str,
        notification_type: NotificationType,
        data: dict[str, str] | None = None,
    ) -> None:
        payload = {"type": notification_type.value, **(data or {})}
        message = Message(
            token=identifier,
            notification=Notification(title=title, body=body),
            data=payload,
        )
        try:
            await asyncio.to_thread(messaging.send, message)
            logger.info(
                "fcm_notification_sent",
                identifier=identifier,
                title=title,
                body=body,
                type=notification_type.value,
                data=payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "fcm_notification_send_failed",
                identifier=identifier,
                title=title,
                body=body,
                error=str(exc),
            )
