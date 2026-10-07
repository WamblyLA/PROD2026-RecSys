from abc import abstractmethod
from typing import Protocol

from app.domain.user.entity import UserId


class MatchDataGateway(Protocol):
    @abstractmethod
    async def list_active_match_user_ids(self, user_id: UserId) -> list[UserId]:
        """Return user_ids of users with whom current user has an active match (mutual latest like)."""
        raise NotImplementedError
