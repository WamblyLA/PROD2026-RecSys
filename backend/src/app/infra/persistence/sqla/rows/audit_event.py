from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.audit_event.value_objects import AuditEventType


class AuditEventRow:
    id: UUID | None
    event_type: AuditEventType | None
    actor_user_id: UUID | None
    target_user_id: UUID | None
    ml_recommendation_id: str | None
    payload: dict[str, Any] | None
    sent_to_ml: bool | None
    created_at: datetime | None
    deleted_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        event_type: AuditEventType | None = None,
        actor_user_id: UUID | None = None,
        target_user_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
        *,
        ml_recommendation_id: str | None = None,
        sent_to_ml: bool | None = None,
        created_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.event_type = event_type
        self.actor_user_id = actor_user_id
        self.target_user_id = target_user_id
        self.payload = payload
        self.ml_recommendation_id = ml_recommendation_id
        self.sent_to_ml = sent_to_ml
        self.created_at = created_at
        self.deleted_at = deleted_at
