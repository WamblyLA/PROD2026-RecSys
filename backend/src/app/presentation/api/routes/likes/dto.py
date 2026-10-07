from datetime import date

from pydantic import BaseModel


class IncomingLikeCandidateProfileResponse(BaseModel):
    first_name: str
    last_name: str | None
    birth_date: date
    gender: str
    region: str | None
    avatar_url: str | None


class IncomingLikeCandidateDatingTraitResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class IncomingLikeCandidateDatingProfileResponse(BaseModel):
    photos: list[str]
    traits: list[IncomingLikeCandidateDatingTraitResponse]


class IncomingLikeCandidateCardResponse(BaseModel):
    user_id: str
    profile: IncomingLikeCandidateProfileResponse | None
    dating_profile: IncomingLikeCandidateDatingProfileResponse | None


class IncomingLikeItemResponse(BaseModel):
    liker_user_id: str
    candidate_card: IncomingLikeCandidateCardResponse | None
    reasons: dict[str, float] | None = None


class IncomingLikesResponse(BaseModel):
    items: list[IncomingLikeItemResponse]
