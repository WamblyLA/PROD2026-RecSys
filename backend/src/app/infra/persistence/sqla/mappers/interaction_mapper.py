from app.domain.interaction.entity import Interaction
from app.domain.interaction.value_objects import InteractionId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import InteractionRow


class InteractionMapper:
    entity_type: type[Interaction] = Interaction

    @staticmethod
    def to_rows(interaction: Interaction) -> list[InteractionRow]:
        return [
            InteractionRow(
                id_=interaction.id,
                actor_user_id=interaction.actor_user_id,
                candidate_user_id=interaction.candidate_user_id,
                action=interaction.action,
                ml_recommendation_id=interaction.ml_recommendation_id,
                created_at=interaction.created_at,
                deleted_at=interaction.deleted_at,
            ),
        ]

    @staticmethod
    def to_entity(row: InteractionRow) -> Interaction:
        if (
            row.id is None
            or row.actor_user_id is None
            or row.candidate_user_id is None
            or row.action is None
            or row.created_at is None
        ):
            msg = "InteractionRow must have id, actor_user_id, candidate_user_id, action, created_at"
            raise ValueError(msg)
        return Interaction(
            id=InteractionId(row.id),
            created_at=row.created_at,
            deleted_at=row.deleted_at,
            actor_user_id=UserId(row.actor_user_id),
            candidate_user_id=UserId(row.candidate_user_id),
            action=row.action,
            ml_recommendation_id=row.ml_recommendation_id,
        )
