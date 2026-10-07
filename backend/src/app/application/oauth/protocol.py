from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OAuthTokenResponse:
    access_token: str
    expires_in: int | None = None


@dataclass(frozen=True, slots=True)
class OAuthUserInfo:
    user_id: str
    email: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None


class OAuthExchangeCodeError(Exception):
    pass


class OAuthLoadUserInfoError(Exception):
    pass


class OAuthClient(Protocol):
    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthTokenResponse:
        raise NotImplementedError

    @abstractmethod
    async def load_user_info(self, access_token: str) -> OAuthUserInfo:
        raise NotImplementedError
