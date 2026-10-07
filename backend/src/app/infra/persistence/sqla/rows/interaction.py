from datetime import datetime
from uuid import UUID

from app.domain.interaction.value_objects import InteractionType


class InteractionRow:
    id: UUID | None
    actor_user_id: UUID | None
    candidate_user_id: UUID | None
    action: InteractionType | None
    ml_recommendation_id: str | None
    created_at: datetime | None
    deleted_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        actor_user_id: UUID | None = None,
        candidate_user_id: UUID | None = None,
        action: InteractionType | None = None,
        ml_recommendation_id: str | None = None,
        created_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.actor_user_id = actor_user_id
        self.candidate_user_id = candidate_user_id
        self.action = action
        self.ml_recommendation_id = ml_recommendation_id
        self.created_at = created_at
        self.deleted_at = deleted_at
