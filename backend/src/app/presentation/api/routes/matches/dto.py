from datetime import date

from pydantic import BaseModel


class MatchCandidateProfileResponse(BaseModel):
    first_name: str
    last_name: str | None
    birth_date: date
    gender: str
    region: str | None
    avatar_url: str | None


class MatchCandidateDatingTraitResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class MatchCandidateDatingProfileResponse(BaseModel):
    photos: list[str]
    traits: list[MatchCandidateDatingTraitResponse]


class MatchCandidateCardResponse(BaseModel):
    user_id: str
    profile: MatchCandidateProfileResponse | None
    dating_profile: MatchCandidateDatingProfileResponse | None


class MatchItemResponse(BaseModel):
    candidate_user_id: str
    candidate_card: MatchCandidateCardResponse | None


class MatchesResponse(BaseModel):
    items: list[MatchItemResponse]
