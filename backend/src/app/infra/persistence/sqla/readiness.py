from typing import override

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.presentation.api.bootstrap.readiness_checker import ReadinessChecker


class SqlaReadinessChecker(ReadinessChecker):
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @override
    async def check(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:  # noqa
            return False
        else:
            return True
