from datetime import datetime
from uuid import UUID


class DatingProfileRow:
    id: UUID | None
    user_id: UUID | None
    created_at: datetime | None
    deleted_at: datetime | None

    def __init__(
        self,
        id_: UUID | None = None,
        user_id: UUID | None = None,
        created_at: datetime | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = id_
        self.user_id = user_id
        self.created_at = created_at
        self.deleted_at = deleted_at


class DatingProfilePhotoRow:
    id: UUID | None
    dating_profile_id: UUID | None
    url: str | None
    position: int | None

    def __init__(
        self,
        id_: UUID | None = None,
        dating_profile_id: UUID | None = None,
        url: str | None = None,
        position: int | None = None,
    ) -> None:
        self.id = id_
        self.dating_profile_id = dating_profile_id
        self.url = url
        self.position = position


class DatingProfileTraitRow:
    id: UUID | None
    dating_profile_id: UUID | None
    trait_code: str | None
    score: float | None
    is_hidden: bool | None

    def __init__(
        self,
        id_: UUID | None = None,
        dating_profile_id: UUID | None = None,
        trait_code: str | None = None,
        score: float | None = None,
        *,
        is_hidden: bool | None = None,
    ) -> None:
        self.id = id_
        self.dating_profile_id = dating_profile_id
        self.trait_code = trait_code
        self.score = score
        self.is_hidden = is_hidden
