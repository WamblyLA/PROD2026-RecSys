from datetime import UTC, datetime
from typing import Any, Self

from uuid_utils.compat import uuid7

from app.domain.audit_event.value_objects import AuditEventId, AuditEventType
from app.domain.common.entity import Entity, entity
from app.domain.user.entity import UserId


@entity
class AuditEvent(Entity[AuditEventId]):
    event_type: AuditEventType
    actor_user_id: UserId | None
    target_user_id: UserId | None
    ml_recommendation_id: str | None
    payload: dict[str, Any] | None
    sent_to_ml: bool

    @classmethod
    def factory(
        cls,
        event_type: AuditEventType,
        actor_user_id: UserId | None = None,
        target_user_id: UserId | None = None,
        payload: dict[str, Any] | None = None,
        ml_recommendation_id: str | None = None,
    ) -> Self:
        return cls(
            id=AuditEventId(uuid7()),
            created_at=datetime.now(tz=UTC),
            event_type=event_type,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            ml_recommendation_id=ml_recommendation_id,
            payload=payload,
            sent_to_ml=False,
        )
