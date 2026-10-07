from typing import Final, override

import aioboto3
from uuid_utils.compat import uuid7

from app.application.dating_profile.photo_storage import DatingPhotoStorage
from app.domain.user.entity import UserId
from app.presentation.api.config.models import S3Config

CONTENT_TYPE_EXTENSIONS: Final[dict[str, str]] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class YandexS3DatingPhotoStorage(DatingPhotoStorage):
    def __init__(self, *, config: S3Config) -> None:
        self._config = config
        self._session = aioboto3.Session(
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    @override
    async def upload_photo(
        self,
        *,
        user_id: UserId,
        content: bytes,
        content_type: str,
    ) -> str:
        extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
        if extension is None:
            msg = f"Unsupported photo content type for storage: {content_type!r}"
            raise ValueError(msg)

        key = f"users/{user_id}/photos/{uuid7()}.{extension}"
        async with self._session.client(
            "s3",
            endpoint_url=self._config.endpoint_url,
        ) as client:
            await client.put_object(
                Bucket=self._config.bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        base_url = self._config.public_base_url.rstrip("/")
        return f"{base_url}/{key}"
