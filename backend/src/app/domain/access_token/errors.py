from dataclasses import dataclass
from typing import override


@dataclass(frozen=True, slots=True)
class AccessTokenExpiredError(Exception):
    token_id: str

    @override
    def __str__(self) -> str:
        return f"Access token id={self.token_id!r} expired"
