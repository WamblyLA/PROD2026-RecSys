from abc import abstractmethod
from typing import Protocol


class PersistenceBootstrapper(Protocol):
    @abstractmethod
    async def bootstrap(self) -> None:
        raise NotImplementedError
