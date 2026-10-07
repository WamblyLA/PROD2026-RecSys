from abc import abstractmethod
from typing import Protocol


class PasswordHasher(Protocol):
    @abstractmethod
    def hash(self, password: str) -> str:
        raise NotImplementedError


class PasswordVerifier(Protocol):
    @abstractmethod
    def verify(
        self,
        verifiable_password: str,
        hashed_password: str,
    ) -> bool:
        raise NotImplementedError
