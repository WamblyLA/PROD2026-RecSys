from typing import override

from litestar import Request

from app.application.access_token.cryptographer import AccessTokenCryptographer
from app.application.access_token.data_gateway import AccessTokenDataGateway
from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.common.identity_provider import IdentityProvider
from app.application.user.data_gateway import UserDataGateway
from app.domain.access_token.entity import AccessTokenId
from app.domain.user.entity import User

AUTH_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "


class LitestarIdentityProvider(IdentityProvider):
    def __init__(
        self,
        request: Request,  # type: ignore[type-arg]
        user_data_gateway: UserDataGateway,
        access_token_data_gateway: AccessTokenDataGateway,
        access_token_cryptographer: AccessTokenCryptographer,
    ) -> None:
        self._request = request
        self._user_data_gateway = user_data_gateway
        self._access_token_data_gateway = access_token_data_gateway
        self._access_token_cryptographer = access_token_cryptographer

    @override
    async def get_current_user(self) -> User:
        access_token_id = self._parse_token()
        if access_token_id is None:
            raise UserUnauthorizedError

        access_token = await self._access_token_data_gateway.load_with_id(access_token_id)
        if access_token is None:
            raise UserUnauthorizedError

        access_token.ensure_not_expired()

        user = await self._user_data_gateway.load_with_id(access_token.user_id)
        if user is None:
            raise UserUnauthorizedError

        return user

    def _parse_token(self) -> AccessTokenId | None:
        authorization = self._request.headers.get(AUTH_HEADER)
        if not authorization or not authorization.startswith(BEARER_PREFIX):
            return None
        token = authorization[len(BEARER_PREFIX) :].strip()
        if not token:
            return None
        return self._access_token_cryptographer.decrypto(token)
