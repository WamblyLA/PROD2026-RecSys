from app.application.common.dto import dto
from app.domain.dating_profile.entity import DatingProfile


@dto
class DatingProfileResult:
    dating_profile: DatingProfile


@dto
class UploadDatingProfilePhotoResult:
    photo_url: str
