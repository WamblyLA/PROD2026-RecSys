from app.domain.recommendation.entity import Recommendation
from app.domain.recommendation.value_objects import RecommendationId, RecommendationReason
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import RecommendationRow


class RecommendationMapper:
    entity_type: type[Recommendation] = Recommendation

    @staticmethod
    def to_rows(recommendation: Recommendation) -> list[RecommendationRow]:
        return [
            RecommendationRow(
                id_=recommendation.id,
                ml_recommendation_id=recommendation.ml_recommendation_id,
                user_id=recommendation.user_id,
                candidate_user_id=recommendation.candidate_user_id,
                reasons={reason.feature_name: reason.score for reason in recommendation.reasons},
                created_at=recommendation.created_at,
            ),
        ]

    @staticmethod
    def to_entity(row: RecommendationRow) -> Recommendation:
        if (
            row.id is None
            or row.ml_recommendation_id is None
            or row.user_id is None
            or row.candidate_user_id is None
            or row.reasons is None
            or row.created_at is None
        ):
            msg = (
                "RecommendationRow must have id, ml_recommendation_id, user_id, candidate_user_id, reasons, created_at"
            )
            raise ValueError(msg)
        return Recommendation(
            id=RecommendationId(row.id),
            ml_recommendation_id=row.ml_recommendation_id,
            user_id=UserId(row.user_id),
            candidate_user_id=UserId(row.candidate_user_id),
            reasons=[
                RecommendationReason(
                    feature_name=str(feature_name),
                    score=float(score),
                )
                for feature_name, score in row.reasons.items()
            ],
            created_at=row.created_at,
            deleted_at=None,
        )
