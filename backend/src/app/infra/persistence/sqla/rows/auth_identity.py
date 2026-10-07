from datetime import datetime
from uuid import UUID

from app.domain.auth_identity.value_objects import AuthMethod


class AuthIdentityRow:
    id: UUID | None
    user_id: UUID | None
    method: AuthMethod | None
    identifier: str | None
    secret_key: str | None
    deleted_at: datetime | None
    created_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        user_id: UUID | None = None,
        method: AuthMethod | None = None,
        identifier: str | None = None,
        secret_key: str | None = None,
        deleted_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.user_id = user_id
        self.method = method
        self.identifier = identifier
        self.secret_key = secret_key
        self.deleted_at = deleted_at
        self.created_at = created_at
