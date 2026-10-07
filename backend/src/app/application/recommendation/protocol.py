from abc import abstractmethod
from typing import Protocol

from app.application.recommendation.dto import RecommendationItem
from app.domain.user.entity import UserId


class RecommendationProvider(Protocol):
    @abstractmethod
    async def get_recommendations(self, *, user_id: UserId) -> list[RecommendationItem]:
        raise NotImplementedError
