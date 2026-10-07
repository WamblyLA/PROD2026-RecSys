from datetime import UTC, datetime
from typing import NewType, Self
from uuid import UUID

from uuid_utils.compat import uuid7

from app.domain.common.entity import Entity, entity
from app.domain.user.value_objects import Profile

UserId = NewType("UserId", UUID)


@entity
class User(Entity[UserId]):
    profile: Profile | None = None

    @classmethod
    def factory(cls) -> Self:
        return cls(
            id=UserId(uuid7()),
            created_at=datetime.now(tz=UTC),
        )
