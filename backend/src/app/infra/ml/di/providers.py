from dishka import BaseScope, Provider, Scope, provide

from app.application.dating_profile.photo_moderation import PhotoModerationService
from app.application.recommendation.protocol import RecommendationProvider
from app.application.user.data_gateway import UserDataGateway
from app.infra.ml.http_photo_moderation_service import HttpPhotoModerationService
from app.infra.ml.http_recommendation_provider import HttpRecommendationProvider
from app.infra.ml.mock_photo_moderation_service import MockPhotoModerationService
from app.infra.ml.mock_recommendation_provider import MockRecommendationProvider
from app.presentation.api.config.models import MlConfig


class RecommendationProviderInfraProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    @provide(scope=Scope.REQUEST)
    def recommendation_provider(
        self,
        config: MlConfig,
        user_gateway: UserDataGateway,
    ) -> RecommendationProvider:
        if config.recommendation_provider == "mock":
            return MockRecommendationProvider(user_gateway=user_gateway)
        if config.recommendation_provider == "http":
            return HttpRecommendationProvider(base_url=config.base_url)
        msg = f"Unknown ML recommendation provider: {config.recommendation_provider!r}"
        raise ValueError(msg)


class PhotoModerationProviderInfraProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    @provide(scope=Scope.REQUEST)
    def photo_moderation_service(self, config: MlConfig) -> PhotoModerationService:
        if config.photo_moderation_provider == "mock":
            return MockPhotoModerationService()
        if config.photo_moderation_provider == "http":
            return HttpPhotoModerationService(base_url=config.base_url)
        msg = f"Unknown ML photo moderation provider: {config.photo_moderation_provider!r}"
        raise ValueError(msg)


providers = [
    RecommendationProviderInfraProvider(),
    PhotoModerationProviderInfraProvider(),
]
