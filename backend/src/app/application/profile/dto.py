from app.application.common.dto import dto
from app.domain.dating_profile.entity import DatingProfile
from app.domain.user.value_objects import Profile


@dto
class ProfileResult:
    user_id: str
    profile: Profile


@dto
class SelfCardResult:
    user_id: str
    profile: Profile | None
    dating_profile: DatingProfile | None
