from datetime import date

from pydantic import BaseModel


class RecommendationCandidateProfileResponse(BaseModel):
    first_name: str
    last_name: str | None
    birth_date: date
    region: str | None
    avatar_url: str | None


class RecommendationCandidateDatingTraitResponse(BaseModel):
    trait_code: str
    score: float
    is_hidden: bool


class RecommendationCandidateDatingProfileResponse(BaseModel):
    photos: list[str]
    traits: list[RecommendationCandidateDatingTraitResponse]


class RecommendationCandidateCardResponse(BaseModel):
    user_id: str
    profile: RecommendationCandidateProfileResponse | None
    dating_profile: RecommendationCandidateDatingProfileResponse | None


class RecommendationResponse(BaseModel):
    ml_recommendation_id: str
    user_id: str
    candidate_user_id: str
    reasons: dict[str, float]
    candidate_card: RecommendationCandidateCardResponse | None


class RecommendationsResponse(BaseModel):
    items: list[RecommendationResponse]
