from typing import override

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interaction.blocked_pairs_gateway import BlockedPairsGateway
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.tables import interaction_table


class DefaultBlockedPairsGateway(BlockedPairsGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def list_blocked_user_ids(self, user_id: UserId) -> set[UserId]:
        latest_block_unblock = (
            select(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
                interaction_table.c.action,
            )
            .where(interaction_table.c.deleted_at.is_(None))
            .where(interaction_table.c.action.in_((InteractionType.BLOCK, InteractionType.UNBLOCK)))
            .order_by(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
                interaction_table.c.created_at.desc(),
            )
            .distinct(
                interaction_table.c.actor_user_id,
                interaction_table.c.candidate_user_id,
            )
            .subquery("latest_block_unblock")
        )

        out_blocked = (
            select(latest_block_unblock.c.candidate_user_id.label("other_id"))
            .where(latest_block_unblock.c.actor_user_id == user_id)
            .where(latest_block_unblock.c.action == InteractionType.BLOCK)
        )
        in_blocked = (
            select(latest_block_unblock.c.actor_user_id.label("other_id"))
            .where(latest_block_unblock.c.candidate_user_id == user_id)
            .where(latest_block_unblock.c.action == InteractionType.BLOCK)
        )
        stmt = union(out_blocked, in_blocked)

        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return {UserId(row[0]) for row in rows if row[0] is not None}
