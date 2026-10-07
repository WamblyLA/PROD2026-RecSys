from typing import override

from app.application.recommendation.dto import RecommendationItem
from app.application.recommendation.errors import RecommendationProviderUnavailableError
from app.application.recommendation.protocol import RecommendationProvider
from app.application.user.data_gateway import UserDataGateway
from app.domain.user.entity import UserId

_MOCK_RECOMMENDATION_LIMIT = 10


class MockRecommendationProvider(RecommendationProvider):
    def __init__(self, user_gateway: UserDataGateway) -> None:
        self._user_gateway = user_gateway

    @override
    async def get_recommendations(self, *, user_id: UserId) -> list[RecommendationItem]:
        try:
            candidate_ids = await self._user_gateway.list_user_ids(
                exclude_user_id=user_id,
            )
        except Exception as error:
            raise RecommendationProviderUnavailableError from error
        current_value = int(user_id)
        candidate_ids = sorted(
            candidate_ids,
            key=lambda candidate_id: abs(int(candidate_id) - current_value),
        )[:_MOCK_RECOMMENDATION_LIMIT]
        return [
            RecommendationItem(
                ml_recommendation_id=f"mock-{user_id}-{i + 1}",
                user_id=str(user_id),
                candidate_user_id=str(cid),
                reasons={"lifestyle": 1.0 - (i * 0.01)},
            )
            for i, cid in enumerate(candidate_ids)
        ]
