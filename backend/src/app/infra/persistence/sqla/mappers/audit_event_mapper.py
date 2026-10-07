from app.domain.audit_event.entity import AuditEvent
from app.domain.audit_event.value_objects import AuditEventId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import AuditEventRow


class AuditEventMapper:
    entity_type: type[AuditEvent] = AuditEvent

    @staticmethod
    def to_rows(event: AuditEvent) -> list[AuditEventRow]:
        return [
            AuditEventRow(
                id_=event.id,
                event_type=event.event_type,
                actor_user_id=event.actor_user_id,
                target_user_id=event.target_user_id,
                ml_recommendation_id=event.ml_recommendation_id,
                payload=event.payload,
                sent_to_ml=event.sent_to_ml,
                created_at=event.created_at,
                deleted_at=event.deleted_at,
            ),
        ]

    @staticmethod
    def to_entity(row: AuditEventRow) -> AuditEvent:
        if row.id is None or row.event_type is None or row.sent_to_ml is None or row.created_at is None:
            msg = "AuditEventRow must have id, event_type, sent_to_ml, created_at"
            raise ValueError(msg)
        return AuditEvent(
            id=AuditEventId(row.id),
            event_type=row.event_type,
            actor_user_id=UserId(row.actor_user_id) if row.actor_user_id is not None else None,
            target_user_id=UserId(row.target_user_id) if row.target_user_id is not None else None,
            ml_recommendation_id=row.ml_recommendation_id,
            payload=row.payload,
            sent_to_ml=row.sent_to_ml,
            created_at=row.created_at,
            deleted_at=row.deleted_at,
        )
