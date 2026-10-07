from abc import abstractmethod
from typing import Protocol

from app.domain.user.entity import User


class IdentityProvider(Protocol):
    @abstractmethod
    async def get_current_user(self) -> User:
        raise NotImplementedError
