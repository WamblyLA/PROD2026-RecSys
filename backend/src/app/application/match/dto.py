from app.application.common.dto import dto
from app.application.recommendation.dto import RecommendationCandidateCardItem


@dto
class MatchItem:
    candidate_user_id: str
    candidate_card: RecommendationCandidateCardItem | None


@dto
class MatchesResult:
    items: list[MatchItem]
