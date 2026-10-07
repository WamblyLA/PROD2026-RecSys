from datetime import datetime
from uuid import UUID


class AccessTokenRow:
    id: UUID | None
    user_id: UUID | None
    revoked: bool | None
    expires_in: datetime | None
    deleted_at: datetime | None
    created_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        user_id: UUID | None = None,
        *,
        revoked: bool | None = None,
        expires_in: datetime | None = None,
        deleted_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.user_id = user_id
        self.revoked = revoked
        self.expires_in = expires_in
        self.deleted_at = deleted_at
        self.created_at = created_at
