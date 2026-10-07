from typing import NewType
from uuid import UUID

from app.domain.common.value_object import value_object

DatingProfileId = NewType("DatingProfileId", UUID)


@value_object
class UserTrait:
    trait_code: str
    score: float
    is_hidden: bool
