from dataclasses import asdict
from typing import Any, override

import structlog
from dishka import AsyncContainer
from dishka.integrations.litestar import FromDishka, inject_websocket
from litestar import WebSocket, websocket
from litestar.status_codes import WS_1008_POLICY_VIOLATION

from app.application.access_token.cryptographer import AccessTokenCryptographer
from app.application.access_token.data_gateway import AccessTokenDataGateway
from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.chat.dto import ChatMessageItem
from app.application.common.messaging.service import MessageConsumer, MessagingService
from app.application.user.data_gateway import UserDataGateway
from app.domain.user.entity import User

logger = structlog.get_logger(__name__)


class WebSocketChatConsumer(MessageConsumer):
    def __init__(self, websocket: WebSocket[Any, Any, Any], user_id: str) -> None:
        self._websocket = websocket
        self._user_id = user_id

    @override
    async def deliver(self, message: ChatMessageItem) -> None:
        payload = {
            "type": "message",
            **asdict(message),
        }
        await self._websocket.send_json(payload)
        logger.info("websocket chat message delivered", message=message)


async def _authenticate_websocket_user(
    token: str,
    user_data_gateway: UserDataGateway,
    access_token_data_gateway: AccessTokenDataGateway,
    access_token_cryptographer: AccessTokenCryptographer,
) -> User:
    access_token_id = access_token_cryptographer.decrypto(token)
    if access_token_id is None:
        raise UserUnauthorizedError

    access_token = await access_token_data_gateway.load_with_id(access_token_id)
    if access_token is None:
        raise UserUnauthorizedError

    access_token.ensure_not_expired()

    user = await user_data_gateway.load_with_id(access_token.user_id)
    if user is None:
        raise UserUnauthorizedError

    return user


@websocket(path="/chat/stream")
@inject_websocket
async def chat_websocket_handler(
    socket: WebSocket[Any, Any, Any],
    container: FromDishka[AsyncContainer],
) -> None:
    await socket.accept()

    async with container() as request_container:
        messaging_service: MessagingService = await request_container.get(MessagingService)
        user_data_gateway: UserDataGateway = await request_container.get(UserDataGateway)
        access_token_data_gateway: AccessTokenDataGateway = await request_container.get(AccessTokenDataGateway)
        access_token_cryptographer: AccessTokenCryptographer = await request_container.get(AccessTokenCryptographer)

        token = socket.query_params.get("token")
        if not token:
            await socket.close(code=WS_1008_POLICY_VIOLATION)
            return

        try:
            user = await _authenticate_websocket_user(
                token=token,
                user_data_gateway=user_data_gateway,
                access_token_data_gateway=access_token_data_gateway,
                access_token_cryptographer=access_token_cryptographer,
            )
        except UserUnauthorizedError:
            await socket.close(code=WS_1008_POLICY_VIOLATION)
            return

        logger.info("websocket successfully authenticated", user_id=user.id)
        consumer = WebSocketChatConsumer(socket, str(user.id))
        messaging_service.register(user.id, consumer)

        try:
            while True:
                _ = await socket.receive_json()
        finally:
            messaging_service.unregister(user.id, consumer)
