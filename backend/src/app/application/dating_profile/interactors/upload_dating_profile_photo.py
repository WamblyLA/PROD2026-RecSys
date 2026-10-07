from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.dating_profile.dto import UploadDatingProfilePhotoResult
from app.application.dating_profile.errors import (
    PhotoStorageUnavailableError,
    PhotoValidationError,
)
from app.application.dating_profile.photo_storage import DatingPhotoStorage

MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@interactor
class UploadDatingProfilePhotoInteractor:
    identity_provider: IdentityProvider
    photo_storage: DatingPhotoStorage

    async def execute(
        self,
        *,
        content: bytes,
        content_type: str,
    ) -> UploadDatingProfilePhotoResult:
        current_user = await self.identity_provider.get_current_user()

        if not content:
            raise PhotoValidationError
        if len(content) > MAX_PHOTO_SIZE_BYTES:
            raise PhotoValidationError
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise PhotoValidationError

        try:
            photo_url = await self.photo_storage.upload_photo(
                user_id=current_user.id,
                content=content,
                content_type=content_type,
            )
        except Exception as error:
            raise PhotoStorageUnavailableError from error
        return UploadDatingProfilePhotoResult(photo_url=photo_url)
