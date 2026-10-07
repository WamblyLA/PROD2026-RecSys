from typing import NewType
from uuid import UUID

from app.domain.common.value_object import value_object

RecommendationId = NewType("RecommendationId", UUID)


@value_object
class RecommendationReason:
    feature_name: str
    score: float
