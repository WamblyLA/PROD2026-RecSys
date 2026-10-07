from abc import abstractmethod
from typing import Protocol


class ReadinessChecker(Protocol):
    @abstractmethod
    async def check(self) -> bool:
        raise NotImplementedError
