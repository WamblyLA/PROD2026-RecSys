from abc import abstractmethod
from typing import Protocol

from app.domain.access_token.entity import AccessToken
from app.domain.user.entity import UserId


class AccessTokenFactory(Protocol):
    @abstractmethod
    def execute(self, user_id: UserId) -> AccessToken:
        raise NotImplementedError
