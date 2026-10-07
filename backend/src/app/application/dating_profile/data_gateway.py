from abc import abstractmethod
from typing import Protocol

from app.domain.dating_profile.entity import DatingProfile
from app.domain.dating_profile.value_objects import DatingProfileId
from app.domain.user.entity import UserId


class DatingProfileDataGateway(Protocol):
    @abstractmethod
    async def load_by_user_id(self, user_id: UserId) -> DatingProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def load_many_by_user_ids(self, user_ids: list[UserId]) -> dict[UserId, DatingProfile]:
        raise NotImplementedError

    @abstractmethod
    async def delete_photos_by_dating_profile_id(
        self,
        dating_profile_id: DatingProfileId,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_trait_hidden(
        self,
        dating_profile_id: DatingProfileId,
        trait_code: str,
        *,
        is_hidden: bool,
    ) -> None:
        raise NotImplementedError
