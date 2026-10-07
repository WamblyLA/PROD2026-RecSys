from datetime import UTC, datetime
from typing import Self

from uuid_utils.compat import uuid7

from app.domain.auth_identity.value_objects import AuthIdentityId, AuthMethod
from app.domain.common.entity import Entity, entity
from app.domain.user.entity import UserId


@entity
class AuthIdentity(Entity[AuthIdentityId]):
    user_id: UserId
    method: AuthMethod
    identifier: str
    secret_key: str | None

    @classmethod
    def factory(
        cls,
        user_id: UserId,
        method: AuthMethod,
        identifier: str,
        secret_key: str | None = None,
    ) -> Self:
        return cls(
            id=AuthIdentityId(uuid7()),
            user_id=user_id,
            method=method,
            identifier=identifier,
            secret_key=secret_key,
            created_at=datetime.now(tz=UTC),
        )
