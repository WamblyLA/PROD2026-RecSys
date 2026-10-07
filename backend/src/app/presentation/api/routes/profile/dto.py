from datetime import date

from pydantic import BaseModel, Field

from app.domain.user.value_objects import Gender


class UpsertProfileRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str | None = Field(None, min_length=1, max_length=80)
    birth_date: date
    gender: Gender
    region: str | None = Field(None, min_length=1, max_length=120)
    avatar_url: str | None = Field(None, max_length=2048)


class ProfileResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str | None
    birth_date: date
    gender: Gender
    region: str | None
    avatar_url: str | None


class CardDatingTraitResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class CardDatingProfileResponse(BaseModel):
    photos: list[str]
    traits: list[CardDatingTraitResponse]


class SelfCardResponse(BaseModel):
    user_id: str
    profile: ProfileResponse | None
    dating_profile: CardDatingProfileResponse | None
