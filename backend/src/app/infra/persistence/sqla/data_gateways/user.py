from typing import override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.user.data_gateway import UserDataGateway
from app.domain.user.entity import User, UserId
from app.infra.persistence.sqla.mappers.user_mapper import UserMapper
from app.infra.persistence.sqla.rows import ProfileRow, UserRow
from app.infra.persistence.sqla.tables import profile_table, user_table


class DefaultUserDataGateway(UserDataGateway):
    def __init__(self, session: AsyncSession, user_mapper: UserMapper) -> None:
        self._session = session
        self._user_mapper = user_mapper

    @override
    async def load_with_id(self, user_id: UserId) -> User | None:
        user_result = await self._session.execute(
            select(UserRow).where(user_table.c.id == user_id),
        )
        user_row = user_result.scalar_one_or_none()
        if user_row is None:
            return None
        profile_result = await self._session.execute(
            select(ProfileRow).where(profile_table.c.user_id == user_id),
        )
        profile_row = profile_result.scalar_one_or_none()
        return self._user_mapper.to_entity(user_row, profile_row)

    @override
    async def list_user_ids(
        self,
        exclude_user_id: UserId | None = None,
    ) -> list[UserId]:
        stmt = select(user_table.c.id).order_by(user_table.c.id)
        if exclude_user_id is not None:
            stmt = stmt.where(user_table.c.id != exclude_user_id)
        result = await self._session.execute(stmt)
        return [UserId(row[0]) for row in result.all()]

    @override
    async def list_random_user_ids(self, limit: int) -> list[UserId]:
        if limit <= 0:
            return []
        stmt = select(user_table.c.id).order_by(func.random()).limit(limit)
        result = await self._session.execute(stmt)
        return [UserId(row[0]) for row in result.all()]

    @override
    async def load_many_with_ids(self, user_ids: list[UserId]) -> list[User]:
        if not user_ids:
            return []

        user_rows_result = await self._session.execute(
            select(UserRow).where(user_table.c.id.in_(user_ids)),
        )
        user_rows = list(user_rows_result.scalars().all())
        if not user_rows:
            return []

        profile_rows_result = await self._session.execute(
            select(ProfileRow).where(profile_table.c.user_id.in_(user_ids)),
        )
        profile_rows = list(profile_rows_result.scalars().all())
        profile_by_user_id = {
            UserId(profile_row.user_id): profile_row for profile_row in profile_rows if profile_row.user_id
        }

        user_by_id = {UserId(user_row.id): user_row for user_row in user_rows if user_row.id}
        return [
            self._user_mapper.to_entity(
                user_row,
                profile_by_user_id.get(user_id),
            )
            for user_id in user_ids
            if (user_row := user_by_id.get(user_id)) is not None
        ]
