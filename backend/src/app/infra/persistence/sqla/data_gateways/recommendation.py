from typing import cast, override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.recommendation.data_gateway import RecommendationDataGateway
from app.application.recommendation.dto import RecommendationItem
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.tables import recommendation_table


class DefaultRecommendationDataGateway(RecommendationDataGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def has_recommendation(
        self,
        *,
        user_id: UserId,
        candidate_user_id: UserId,
        ml_recommendation_id: str | None = None,
    ) -> bool:
        stmt = select(recommendation_table.c.id).where(
            recommendation_table.c.user_id == user_id,
            recommendation_table.c.candidate_user_id == candidate_user_id,
        )
        if ml_recommendation_id is not None:
            stmt = stmt.where(recommendation_table.c.ml_recommendation_id == ml_recommendation_id)
        stmt = stmt.limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def load_latest_for_pair(
        self,
        *,
        user_id: UserId,
        candidate_user_id: UserId,
    ) -> RecommendationItem | None:
        stmt = (
            select(
                recommendation_table.c.ml_recommendation_id,
                recommendation_table.c.user_id,
                recommendation_table.c.candidate_user_id,
                recommendation_table.c.reasons,
                recommendation_table.c.created_at,
            )
            .where(
                recommendation_table.c.user_id == user_id,
                recommendation_table.c.candidate_user_id == candidate_user_id,
            )
            .order_by(recommendation_table.c.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None

        ml_recommendation_id, rec_user_id, rec_candidate_user_id, reasons, _created_at = row
        return RecommendationItem(
            ml_recommendation_id=ml_recommendation_id,
            user_id=str(rec_user_id),
            candidate_user_id=str(rec_candidate_user_id),
            reasons=cast("dict[str, float]", reasons),
            candidate_card=None,
        )
