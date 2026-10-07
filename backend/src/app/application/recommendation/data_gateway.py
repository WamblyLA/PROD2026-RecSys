from abc import abstractmethod
from typing import Protocol

from app.application.recommendation.dto import RecommendationItem
from app.domain.user.entity import UserId


class RecommendationDataGateway(Protocol):
    @abstractmethod
    async def has_recommendation(
        self,
        *,
        user_id: UserId,
        candidate_user_id: UserId,
        ml_recommendation_id: str | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def load_latest_for_pair(
        self,
        *,
        user_id: UserId,
        candidate_user_id: UserId,
    ) -> RecommendationItem | None:
        raise NotImplementedError
