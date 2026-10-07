from abc import abstractmethod
from typing import Protocol

from app.domain.user.entity import UserId


class BlockedPairsGateway(Protocol):
    """Read-only: which user_ids are in a blocked state with the given user (either direction)."""

    @abstractmethod
    async def list_blocked_user_ids(self, user_id: UserId) -> set[UserId]:
        """Users blocked with user_id: either user_id blocked them or they blocked user_id (latest action = block)."""
        raise NotImplementedError
