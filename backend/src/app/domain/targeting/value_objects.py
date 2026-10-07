from enum import StrEnum

from app.domain.common.value_object import value_object


class TargetGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    BOTH = "both"


@value_object
class TargetingRules:
    region: str | None
    gender_target: TargetGender
    age_from: int
    age_to: int
