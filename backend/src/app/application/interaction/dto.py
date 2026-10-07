from datetime import datetime

from app.application.common.dto import dto
from app.domain.interaction.value_objects import InteractionId, InteractionType
from app.domain.user.entity import UserId


@dto
class InteractionResult:
    interaction_id: InteractionId
    actor_user_id: UserId
    candidate_user_id: UserId
    action: InteractionType
    ml_recommendation_id: str | None
    created_at: datetime
