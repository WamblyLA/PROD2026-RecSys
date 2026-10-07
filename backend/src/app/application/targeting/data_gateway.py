from abc import abstractmethod
from typing import Protocol

from app.domain.targeting.entity import Targeting
from app.domain.user.entity import UserId


class TargetingDataGateway(Protocol):
    @abstractmethod
    async def load_by_user_id(self, user_id: UserId) -> Targeting | None:
        raise NotImplementedError
