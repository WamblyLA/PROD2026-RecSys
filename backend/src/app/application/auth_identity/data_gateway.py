from abc import abstractmethod
from typing import Protocol

from app.domain.auth_identity.entity import AuthIdentity
from app.domain.auth_identity.value_objects import AuthMethod


class AuthIdentityDataGateway(Protocol):
    @abstractmethod
    async def load_by_method_and_identifier(
        self,
        method: AuthMethod,
        identifier: str,
    ) -> AuthIdentity | None:
        raise NotImplementedError
