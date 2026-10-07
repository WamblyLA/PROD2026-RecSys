from datetime import datetime
from uuid import UUID

from app.domain.targeting.value_objects import TargetGender

_DEFAULT_DATETIME = datetime.min.replace(tzinfo=None)


class TargetingRow:
    user_id: UUID | None
    region: str | None
    gender_target: TargetGender
    age_from: int
    age_to: int
    created_at: datetime | None
    updated_at: datetime | None

    def __init__(
        self,
        user_id: UUID | None = None,
        region: str | None = None,
        gender_target: TargetGender = TargetGender.BOTH,
        age_from: int = 18,
        age_to: int = 99,
        created_at: datetime | None = _DEFAULT_DATETIME,
        updated_at: datetime | None = None,
    ) -> None:
        self.user_id = user_id
        self.region = region
        self.gender_target = gender_target
        self.age_from = age_from
        self.age_to = age_to
        self.created_at = created_at
        self.updated_at = updated_at
