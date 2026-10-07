from datetime import datetime
from uuid import UUID


class RecommendationRow:
    id: UUID | None
    ml_recommendation_id: str | None
    user_id: UUID | None
    candidate_user_id: UUID | None
    reasons: dict[str, float] | None
    created_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        ml_recommendation_id: str | None = None,
        user_id: UUID | None = None,
        candidate_user_id: UUID | None = None,
        reasons: dict[str, float] | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.ml_recommendation_id = ml_recommendation_id
        self.user_id = user_id
        self.candidate_user_id = candidate_user_id
        self.reasons = reasons
        self.created_at = created_at
