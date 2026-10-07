from abc import abstractmethod
from typing import Protocol

from app.domain.user.entity import UserId


class IncomingLikesDataGateway(Protocol):
    """Users who liked me (latest B->me = like) and to whom I have not replied (no like/dislike from me to them)."""

    @abstractmethod
    async def list_liker_user_ids(self, user_id: UserId) -> list[UserId]:
        raise NotImplementedError
