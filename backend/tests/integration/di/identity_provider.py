from typing import override

from app.application.auth_identity.errors import UserUnauthorizedError
from app.application.common.identity_provider import IdentityProvider
from app.domain.user.entity import User


class MockIdentityProvider(IdentityProvider):
    def __init__(self) -> None:
        self._user: User | None = None

    def set_user(self, user: User) -> None:
        self._user = user

    @override
    async def get_current_user(self) -> User:
        if self._user is None:
            raise UserUnauthorizedError
        return self._user
