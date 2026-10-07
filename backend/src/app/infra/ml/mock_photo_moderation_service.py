from typing import override

from app.application.dating_profile.photo_moderation import PhotoModerationService


class MockPhotoModerationService(PhotoModerationService):
    @override
    async def ensure_photo_allowed(
        self,
        *,
        content: bytes,
        content_type: str,
    ) -> None:
        _ = (content, content_type)
