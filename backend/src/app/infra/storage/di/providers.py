from dishka import BaseScope, Provider, Scope, provide

from app.application.dating_profile.photo_storage import DatingPhotoStorage
from app.infra.storage.yandex_s3_dating_photo_storage import YandexS3DatingPhotoStorage
from app.presentation.api.config.models import S3Config


class DatingPhotoStorageProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide
    def dating_photo_storage(self, config: S3Config) -> DatingPhotoStorage:
        return YandexS3DatingPhotoStorage(config=config)


providers = [
    DatingPhotoStorageProvider(),
]
