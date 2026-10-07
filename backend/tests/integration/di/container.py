from dishka import STRICT_VALIDATION, AsyncContainer, BaseScope, Provider, Scope, make_async_container, provide

from app.application.auth_identity.di.providers import providers as auth_identity_providers
from app.application.chat.di.providers import providers as chat_providers
from app.application.common.identity_provider import IdentityProvider
from app.application.common.messaging.di.providers import providers as messaging_providers
from app.application.dating_profile.di.providers import providers as dating_profile_providers
from app.application.incoming_likes.di.providers import providers as incoming_likes_providers
from app.application.interaction.di.providers import providers as interaction_providers
from app.application.match.di.providers import providers as match_providers
from app.application.notification_device.di.providers import providers as notification_device_providers
from app.application.profile.di.providers import providers as profile_providers
from app.application.recommendation.di.providers import providers as recommendation_providers
from app.application.recommendation.protocol import RecommendationProvider
from app.application.targeting.di.providers import providers as targeting_providers
from app.application.user.data_gateway import UserDataGateway
from app.infra.config.di.providers import providers as config_providers
from app.infra.ml.di.providers import PhotoModerationProviderInfraProvider
from app.infra.ml.http_recommendation_provider import HttpRecommendationProvider
from app.infra.ml.mock_recommendation_provider import MockRecommendationProvider
from app.infra.notifications.di.providers import providers as notification_providers
from app.infra.oauth.di.providers import providers as oauth_providers
from app.infra.persistence.sqla.di.providers import providers as sqla_providers
from app.infra.security.di.providers import providers as security_providers
from app.infra.storage.di.providers import providers as storage_providers
from tests.integration.di.identity_provider import MockIdentityProvider


class MockIdentityProviderProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    @provide(scope=Scope.REQUEST)
    def identity_provider(self) -> IdentityProvider:
        return MockIdentityProvider()


class HttpRecommendationProviderForTests(Provider):
    scope: BaseScope | None = Scope.REQUEST

    def __init__(self, *, base_url: str) -> None:
        super().__init__()
        self._base_url = base_url

    @provide(scope=Scope.REQUEST)
    def recommendation_provider(self) -> RecommendationProvider:
        return HttpRecommendationProvider(base_url=self._base_url)


class MockRecommendationProviderForTests(Provider):
    scope: BaseScope | None = Scope.REQUEST

    @provide(scope=Scope.REQUEST)
    def recommendation_provider(self, user_gateway: UserDataGateway) -> RecommendationProvider:
        return MockRecommendationProvider(user_gateway=user_gateway)


def build_test_container() -> AsyncContainer:
    return make_async_container(
        *config_providers,
        *sqla_providers,
        *security_providers,
        *oauth_providers,
        PhotoModerationProviderInfraProvider(),
        MockRecommendationProviderForTests(),
        *storage_providers,
        *auth_identity_providers,
        *notification_providers,
        MockIdentityProviderProvider(),
        *notification_device_providers,
        *messaging_providers,
        *profile_providers,
        *recommendation_providers,
        *match_providers,
        *incoming_likes_providers,
        *targeting_providers,
        *dating_profile_providers,
        *interaction_providers,
        *chat_providers,
        validation_settings=STRICT_VALIDATION,
    )


def build_http_ml_test_container(*, base_url: str) -> AsyncContainer:
    return make_async_container(
        *config_providers,
        *sqla_providers,
        *security_providers,
        *oauth_providers,
        PhotoModerationProviderInfraProvider(),
        HttpRecommendationProviderForTests(base_url=base_url),
        *storage_providers,
        *auth_identity_providers,
        *notification_providers,
        MockIdentityProviderProvider(),
        *notification_device_providers,
        *messaging_providers,
        *profile_providers,
        *recommendation_providers,
        *match_providers,
        *incoming_likes_providers,
        *targeting_providers,
        *dating_profile_providers,
        *interaction_providers,
        *chat_providers,
        validation_settings=STRICT_VALIDATION,
    )
