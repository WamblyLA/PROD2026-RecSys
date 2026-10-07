from datetime import UTC, datetime
from typing import Self

from app.domain.common.entity import Entity, entity
from app.domain.targeting.value_objects import TargetingRules
from app.domain.user.entity import UserId


@entity
class Targeting(Entity[UserId]):
    rules: TargetingRules

    @classmethod
    def factory(cls, user_id: UserId, rules: TargetingRules) -> Self:
        return cls(
            id=user_id,
            created_at=datetime.now(tz=UTC),
            rules=rules,
        )
