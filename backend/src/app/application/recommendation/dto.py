from datetime import date

from app.application.common.dto import dto
from app.domain.user.value_objects import Gender


@dto
class RecommendationItem:
    ml_recommendation_id: str
    user_id: str
    candidate_user_id: str
    reasons: dict[str, float]
    candidate_card: "RecommendationCandidateCardItem | None" = None


@dto
class RecommendationCandidateProfileItem:
    first_name: str
    last_name: str | None
    birth_date: date
    gender: Gender
    region: str | None
    avatar_url: str | None


@dto
class RecommendationCandidateDatingTraitItem:
    trait_code: str
    score: float
    is_hidden: bool


@dto
class RecommendationCandidateDatingProfileItem:
    photos: list[str]
    traits: list[RecommendationCandidateDatingTraitItem]


@dto
class RecommendationCandidateCardItem:
    user_id: str
    profile: RecommendationCandidateProfileItem | None
    dating_profile: RecommendationCandidateDatingProfileItem | None


@dto
class RecommendationsResult:
    items: list[RecommendationItem]
