from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.profile.dto import SelfCardResult
from app.application.profile.errors import CardUserNotFoundError
from app.application.user.data_gateway import UserDataGateway
from app.domain.user.entity import UserId


@interactor
class GetUserCardInteractor:
    identity_provider: IdentityProvider
    user_data_gateway: UserDataGateway
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(self, *, user_id: UserId) -> SelfCardResult:
        _ = await self.identity_provider.get_current_user()
        user = await self.user_data_gateway.load_with_id(user_id)
        if user is None:
            raise CardUserNotFoundError
        dating_profile = await self.dating_profile_data_gateway.load_by_user_id(user_id)
        return SelfCardResult(
            user_id=str(user.id),
            profile=user.profile,
            dating_profile=dating_profile,
        )
