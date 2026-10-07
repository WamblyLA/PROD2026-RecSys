from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.dating_profile.dto import DatingProfileResult
from app.application.dating_profile.errors import DatingProfileNotFoundError


@interactor
class GetDatingProfileInteractor:
    identity_provider: IdentityProvider
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(self) -> DatingProfileResult:
        user = await self.identity_provider.get_current_user()
        profile = await self.dating_profile_data_gateway.load_by_user_id(user.id)
        if profile is None:
            raise DatingProfileNotFoundError
        return DatingProfileResult(dating_profile=profile)
