from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.dating_profile.errors import DatingProfileNotFoundError


@interactor
class SetTraitVisibilityInteractor:
    identity_provider: IdentityProvider
    unit_of_work: UnitOfWork
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(
        self,
        trait_code: str,
        *,
        is_hidden: bool,
    ) -> None:
        user = await self.identity_provider.get_current_user()
        profile = await self.dating_profile_data_gateway.load_by_user_id(user.id)
        if profile is None:
            raise DatingProfileNotFoundError
        if not any(t.trait_code == trait_code for t in profile.traits):
            raise DatingProfileNotFoundError
        await self.dating_profile_data_gateway.set_trait_hidden(
            profile.id,
            trait_code,
            is_hidden=is_hidden,
        )
        await self.unit_of_work.commit()
