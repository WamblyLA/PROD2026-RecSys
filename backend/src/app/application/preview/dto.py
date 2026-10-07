from app.application.common.dto import dto
from app.application.recommendation.dto import RecommendationCandidateCardItem


@dto
class PreviewCardsResult:
    cards: list[RecommendationCandidateCardItem]
