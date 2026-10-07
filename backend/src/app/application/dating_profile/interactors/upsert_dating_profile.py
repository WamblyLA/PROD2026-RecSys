from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.application.common.unit_of_work import UnitOfWork
from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.application.dating_profile.dto import DatingProfileResult
from app.application.dating_profile.errors import (
    DatingProfileValidationError,
    ProfileRequiredError,
)
from app.domain.dating_profile.entity import DatingProfile


@interactor
class UpsertDatingProfileInteractor:
    identity_provider: IdentityProvider
    unit_of_work: UnitOfWork
    dating_profile_data_gateway: DatingProfileDataGateway

    async def execute(
        self,
        photos: list[str],
    ) -> DatingProfileResult:
        user = await self.identity_provider.get_current_user()
        if user.profile is None:
            raise ProfileRequiredError
        if len(photos) < 1:
            raise DatingProfileValidationError
        existing = await self.dating_profile_data_gateway.load_by_user_id(user.id)
        if existing is not None:
            await self.dating_profile_data_gateway.delete_photos_by_dating_profile_id(
                existing.id,
            )
            updated = DatingProfile(
                id=existing.id,
                created_at=existing.created_at,
                deleted_at=existing.deleted_at,
                user_id=user.id,
                photos=photos,
                traits=existing.traits,
            )
            await self.unit_of_work.add(updated)
        else:
            profile = DatingProfile.factory(
                user_id=user.id,
                photos=photos,
                traits=[],
            )
            await self.unit_of_work.add(profile)
        await self.unit_of_work.commit()
        final = await self.dating_profile_data_gateway.load_by_user_id(user.id)
        if final is None:
            raise DatingProfileValidationError
        return DatingProfileResult(dating_profile=final)
