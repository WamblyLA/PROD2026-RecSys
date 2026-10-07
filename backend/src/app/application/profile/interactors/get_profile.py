from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.profile.dto import ProfileResult
from app.application.profile.errors import ProfileNotFoundError


@interactor
class GetProfileInteractor:
    identity_provider: IdentityProvider

    async def execute(self) -> ProfileResult:
        user = await self.identity_provider.get_current_user()
        if user.profile is None:
            raise ProfileNotFoundError
        return ProfileResult(user_id=str(user.id), profile=user.profile)
