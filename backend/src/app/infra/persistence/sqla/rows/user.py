from datetime import datetime
from uuid import UUID


class UserRow:
    id: UUID | None
    created_at: datetime | None
    deleted_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        created_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.created_at = created_at
        self.deleted_at = deleted_at
