from datetime import UTC, datetime
from typing import Self

from uuid_utils.compat import uuid7

from app.domain.common.entity import Entity, entity
from app.domain.dating_profile.value_objects import DatingProfileId, UserTrait
from app.domain.user.entity import UserId


@entity
class DatingProfile(Entity[DatingProfileId]):
    user_id: UserId
    photos: list[str]
    traits: list[UserTrait]

    @classmethod
    def factory(
        cls,
        user_id: UserId,
        photos: list[str],
        traits: list[UserTrait] | None = None,
    ) -> Self:
        return cls(
            id=DatingProfileId(uuid7()),
            created_at=datetime.now(tz=UTC),
            user_id=user_id,
            photos=photos,
            traits=traits or [],
        )
