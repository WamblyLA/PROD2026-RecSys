from abc import abstractmethod
from typing import Protocol


class PhotoModerationService(Protocol):
    @abstractmethod
    async def ensure_photo_allowed(
        self,
        *,
        content: bytes,
        content_type: str,
    ) -> None:
        raise NotImplementedError
