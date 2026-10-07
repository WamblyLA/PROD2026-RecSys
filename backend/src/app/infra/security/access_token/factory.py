from datetime import timedelta
from typing import override

from app.application.access_token.entity_factory import AccessTokenFactory
from app.domain.access_token.entity import AccessToken
from app.domain.user.entity import UserId
from app.presentation.api.config.models import AccessTokenConfig


class DefaultAccessTokenFactory(AccessTokenFactory):
    def __init__(self, configuration: AccessTokenConfig) -> None:
        self._configuration = configuration

    @override
    def execute(self, user_id: UserId) -> AccessToken:
        return AccessToken.factory(
            user_id=user_id,
            expires_in=timedelta(seconds=self._configuration.expires_in_seconds),
        )
