from abc import abstractmethod
from typing import Any, Protocol

from app.domain.common.entity import Entity


class UnitOfWork(Protocol):
    @abstractmethod
    async def add(self, *entities: Entity[Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError
