from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.dating_profile.interactors.get_dating_profile import (
    GetDatingProfileInteractor,
)
from app.application.dating_profile.interactors.set_trait_visibility import (
    SetTraitVisibilityInteractor,
)
from app.application.dating_profile.interactors.upload_dating_profile_photo import (
    UploadDatingProfilePhotoInteractor,
)
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)


class DatingProfileInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetDatingProfileInteractor],
        WithParents[UpsertDatingProfileInteractor],
        WithParents[UploadDatingProfilePhotoInteractor],
        WithParents[SetTraitVisibilityInteractor],
    )


providers = [
    DatingProfileInteractorProvider(),
]
