from typing import override

from sqlalchemy.ext.asyncio import AsyncEngine

from app.infra.persistence.sqla.tables import meta_data
from app.presentation.api.bootstrap.persistence_bootstrapper import PersistenceBootstrapper


class SqlaPersistenceBootstrapper(PersistenceBootstrapper):
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @override
    async def bootstrap(self) -> None:
        async with self._engine.begin() as connection:
            await connection.run_sync(meta_data.create_all)
