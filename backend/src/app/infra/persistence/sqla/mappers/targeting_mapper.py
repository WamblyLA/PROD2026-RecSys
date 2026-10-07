from datetime import UTC, datetime

from app.domain.targeting.entity import Targeting
from app.domain.targeting.value_objects import TargetingRules
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import TargetingRow


class TargetingMapper:
    entity_type: type[Targeting] = Targeting

    @staticmethod
    def to_rows(targeting: Targeting) -> list[TargetingRow]:
        now = datetime.now(tz=UTC)
        return [
            TargetingRow(
                user_id=targeting.id,
                region=targeting.rules.region,
                gender_target=targeting.rules.gender_target,
                age_from=targeting.rules.age_from,
                age_to=targeting.rules.age_to,
                created_at=targeting.created_at,
                updated_at=now,
            ),
        ]

    @staticmethod
    def to_entity(row: TargetingRow) -> Targeting:
        if row.user_id is None or row.created_at is None:
            msg = "TargetingRow must have user_id and created_at"
            raise ValueError(msg)
        rules = TargetingRules(
            region=row.region,
            gender_target=row.gender_target,
            age_from=row.age_from,
            age_to=row.age_to,
        )
        return Targeting(
            id=UserId(row.user_id),
            created_at=row.created_at,
            deleted_at=None,
            rules=rules,
        )
