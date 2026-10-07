from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.targeting.data_gateway import TargetingDataGateway
from app.domain.targeting.entity import Targeting
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.mappers.targeting_mapper import TargetingMapper
from app.infra.persistence.sqla.rows import TargetingRow
from app.infra.persistence.sqla.tables import targeting_table


class DefaultTargetingDataGateway(TargetingDataGateway):
    def __init__(
        self,
        session: AsyncSession,
        targeting_mapper: TargetingMapper,
    ) -> None:
        self._session = session
        self._mapper = targeting_mapper

    @override
    async def load_by_user_id(self, user_id: UserId) -> Targeting | None:
        result = await self._session.execute(
            select(TargetingRow).where(targeting_table.c.user_id == user_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._mapper.to_entity(row)
