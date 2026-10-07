from datetime import date, datetime
from uuid import UUID

from app.domain.user.value_objects import Gender

_DEFAULT_DATE = date(1970, 1, 1)
_DEFAULT_DATETIME = datetime.min.replace(tzinfo=None)


class ProfileRow:
    user_id: UUID | None
    first_name: str
    last_name: str | None
    birth_date: date | None
    gender: Gender
    region: str | None
    avatar_url: str | None
    created_at: datetime | None
    updated_at: datetime | None

    def __init__(
        self,
        user_id: UUID | None = None,
        first_name: str = "",
        last_name: str | None = None,
        birth_date: date | None = _DEFAULT_DATE,
        gender: Gender = Gender.MALE,
        region: str | None = None,
        avatar_url: str | None = None,
        created_at: datetime | None = _DEFAULT_DATETIME,
        updated_at: datetime | None = None,
    ) -> None:
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = gender
        self.region = region
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.updated_at = updated_at
