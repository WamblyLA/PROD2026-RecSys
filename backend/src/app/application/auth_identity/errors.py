from dataclasses import dataclass
from typing import override

from app.domain.auth_identity.value_objects import AuthMethod


@dataclass(frozen=True, slots=True)
class UserAlreadyExistsError(Exception):
    identifier: str
    auth_method: AuthMethod

    @override
    def __str__(self) -> str:
        return f"User with identifier={self.identifier!r} and auth method={self.auth_method.value} already exists"


@dataclass(frozen=True, slots=True)
class UserNotFoundError(Exception):
    identifier: str

    @override
    def __str__(self) -> str:
        return f"User with identifier={self.identifier!r} not found"


@dataclass(frozen=True, slots=True)
class InvalidCredentialsError(Exception):
    @override
    def __str__(self) -> str:
        return "Invalid credentials"


@dataclass(frozen=True, slots=True)
class InvalidCodeError(Exception):
    @override
    def __str__(self) -> str:
        return "Invalid authorization code"


@dataclass(frozen=True, slots=True)
class AuthError(Exception):
    @override
    def __str__(self) -> str:
        return "Authentication failed"


@dataclass(frozen=True, slots=True)
class UserUnauthorizedError(Exception):
    @override
    def __str__(self) -> str:
        return "Unauthorized"
