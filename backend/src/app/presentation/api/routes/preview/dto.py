from datetime import date

from pydantic import BaseModel


class PreviewCardProfileResponse(BaseModel):
    first_name: str
    last_name: str | None
    birth_date: date
    gender: str
    region: str | None
    avatar_url: str | None


class PreviewCardDatingTraitResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class PreviewCardDatingProfileResponse(BaseModel):
    photos: list[str]
    traits: list[PreviewCardDatingTraitResponse]


class PreviewCardResponse(BaseModel):
    user_id: str
    profile: PreviewCardProfileResponse | None
    dating_profile: PreviewCardDatingProfileResponse | None


class PreviewCardsResponse(BaseModel):
    cards: list[PreviewCardResponse]
