from dishka.integrations.litestar import DishkaRouter, FromDishka
from litestar import post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from pydantic import BaseModel, Field

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.notification_device.errors import NotificationDeviceNotFoundError
from app.application.notification_device.interactors.register_device import (
    RegisterNotificationDeviceInteractor,
    RegisterNotificationDeviceRequest,
)
from app.application.notification_device.interactors.send_notification import (
    SendNotificationInteractor,
    SendNotificationRequest,
)


class SendNotificationBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    data: dict[str, str] | None = None


class RegisterDeviceBody(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=200)


@post(
    path="/",
    summary="Send push notification",
    security=[{"BearerToken": []}],
)
async def send_notification(
    data: SendNotificationBody,
    interactor: FromDishka[SendNotificationInteractor],
) -> None:
    try:
        await interactor.execute(
            SendNotificationRequest(
                title=data.title,
                body=data.body,
                data=data.data,
            ),
        )
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error
    except NotificationDeviceNotFoundError as error:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Notification device not found") from error


@post(
    path="/devices",
    summary="Register FCM device token",
    security=[{"BearerToken": []}],
)
async def register_notification_device(
    data: RegisterDeviceBody,
    interactor: FromDishka[RegisterNotificationDeviceInteractor],
) -> None:
    try:
        await interactor.execute(RegisterNotificationDeviceRequest(device_id=data.device_id))
    except UserUnauthorizedError as error:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Unauthorized") from error


router = DishkaRouter(
    path="/notifications",
    route_handlers=[send_notification, register_notification_device],
    tags=["notifications"],
)
