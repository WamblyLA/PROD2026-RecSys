from abc import abstractmethod
from typing import Protocol

from app.domain.user.entity import UserId


class DatingPhotoStorage(Protocol):
    @abstractmethod
    async def upload_photo(
        self,
        *,
        user_id: UserId,
        content: bytes,
        content_type: str,
    ) -> str:
        raise NotImplementedError
