from typing import Any, override

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.common.unit_of_work import UnitOfWork
from app.domain.common.entity import Entity
from app.infra.persistence.sqla.mappers import GlobalDataMapper

logger = get_logger(__name__)


class DefaultUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession, data_mapper: GlobalDataMapper) -> None:
        self._session = session
        self._data_mapper = data_mapper
        self._pending: list[Entity[Any]] = []

    @override
    async def add(self, *entities: Entity[Any]) -> None:
        self._pending.extend(entities)

    @override
    async def commit(self) -> None:
        try:
            for entity in self._pending:
                for row in self._data_mapper.to_rows(entity):
                    await self._session.merge(row)
            self._pending.clear()
            await self._session.commit()
        except SQLAlchemyError as exc:  # pragma: no cover - defensive logging
            logger.exception("uow_commit_failed", error=str(exc))
            raise
