from datetime import UTC, datetime
from typing import Self

from uuid_utils.compat import uuid7

from app.domain.common.entity import Entity, entity
from app.domain.recommendation.value_objects import RecommendationId, RecommendationReason
from app.domain.user.entity import UserId


@entity
class Recommendation(Entity[RecommendationId]):
    ml_recommendation_id: str
    user_id: UserId
    candidate_user_id: UserId
    reasons: list[RecommendationReason]

    @classmethod
    def factory(
        cls,
        ml_recommendation_id: str,
        user_id: UserId,
        candidate_user_id: UserId,
        reasons: list[RecommendationReason],
    ) -> Self:
        return cls(
            id=RecommendationId(uuid7()),
            created_at=datetime.now(tz=UTC),
            ml_recommendation_id=ml_recommendation_id,
            user_id=user_id,
            candidate_user_id=candidate_user_id,
            reasons=reasons,
        )
