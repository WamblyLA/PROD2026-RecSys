from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.match.data_gateway import MatchDataGateway
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.tables import interaction_table


class DefaultMatchDataGateway(MatchDataGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def list_active_match_user_ids(self, user_id: UserId) -> list[UserId]:
        latest = (
            select(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
                interaction_table.c.action,
            )
            .where(interaction_table.c.deleted_at.is_(None))
            .order_by(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
                interaction_table.c.created_at.desc(),
            )
            .distinct(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
            )
            .subquery("latest")
        )

        l1 = latest.alias("l1")
        l2 = latest.alias("l2")
        stmt = (
            select(l1.c.candidate_user_id.label("user_id"))
            .select_from(
                l1.join(
                    l2,
                    (l2.c.actor_user_id == l1.c.candidate_user_id) & (l2.c.candidate_user_id == l1.c.actor_user_id),
                ),
            )
            .where(l1.c.actor_user_id == user_id)
            .where(l1.c.action == InteractionType.LIKE)
            .where(l2.c.action == InteractionType.LIKE)
        )

        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return [UserId(row[0]) for row in rows if row[0] is not None]
