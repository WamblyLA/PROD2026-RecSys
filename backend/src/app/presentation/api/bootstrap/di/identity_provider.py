from dishka import BaseScope, Provider, Scope, provide
from litestar import Request

from app.application.access_token.cryptographer import AccessTokenCryptographer
from app.application.access_token.data_gateway import AccessTokenDataGateway
from app.application.common.identity_provider import IdentityProvider
from app.application.user.data_gateway import UserDataGateway
from app.presentation.api.identity_provider import LitestarIdentityProvider


class IdentityProviderProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    @provide
    def identity_provider(
        self,
        request: Request,  # type: ignore[type-arg]
        user_data_gateway: UserDataGateway,
        access_token_data_gateway: AccessTokenDataGateway,
        access_token_cryptographer: AccessTokenCryptographer,
    ) -> IdentityProvider:
        return LitestarIdentityProvider(
            request=request,
            user_data_gateway=user_data_gateway,
            access_token_data_gateway=access_token_data_gateway,
            access_token_cryptographer=access_token_cryptographer,
        )
