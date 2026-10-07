from typing import override

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.incoming_likes.data_gateway import IncomingLikesDataGateway
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.tables import interaction_table


class DefaultIncomingLikesDataGateway(IncomingLikesDataGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def list_liker_user_ids(self, user_id: UserId) -> list[UserId]:
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

        likers_to_me = latest.alias("likers_to_me")
        my_reply = latest.alias("my_reply")
        replied = exists(
            select(1)
            .select_from(my_reply)
            .where(
                my_reply.c.actor_user_id == user_id,
                my_reply.c.candidate_user_id == likers_to_me.c.actor_user_id,
                my_reply.c.action.in_([InteractionType.LIKE, InteractionType.DISLIKE]),
            )
        )
        stmt = (
            select(likers_to_me.c.actor_user_id)
            .select_from(likers_to_me)
            .where(likers_to_me.c.candidate_user_id == user_id)
            .where(likers_to_me.c.action == InteractionType.LIKE)
            .where(~replied)
        )

        result = await self._session.execute(stmt)
        rows = result.fetchall()
        return [UserId(row[0]) for row in rows if row[0] is not None]
