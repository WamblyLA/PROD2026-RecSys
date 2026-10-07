from app.application.common.dto import dto
from app.application.recommendation.dto import RecommendationCandidateCardItem


@dto
class IncomingLikeItem:
    liker_user_id: str
    candidate_card: RecommendationCandidateCardItem | None
    reasons: dict[str, float] | None


@dto
class IncomingLikesResult:
    items: list[IncomingLikeItem]
