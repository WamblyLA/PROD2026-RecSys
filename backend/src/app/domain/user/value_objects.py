from datetime import date
from enum import StrEnum

from app.domain.common.value_object import value_object


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


@value_object
class Profile:
    first_name: str
    last_name: str | None
    birth_date: date
    gender: Gender
    region: str | None
    avatar_url: str | None
