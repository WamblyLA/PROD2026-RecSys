from dishka import BaseScope, Provider, Scope, provide

from app.application.oauth.protocol import OAuthClient
from app.infra.oauth.yandex import YandexOAuthClient
from app.presentation.api.config.models import YandexOAuthConfig


class OAuthProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide(scope=Scope.APP)
    def yandex_oauth_client(
        self,
        config: YandexOAuthConfig,
    ) -> OAuthClient:
        return YandexOAuthClient(config=config)


providers = [
    OAuthProvider(),
]
