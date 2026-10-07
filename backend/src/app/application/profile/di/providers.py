from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.profile.interactors.get_profile import GetProfileInteractor
from app.application.profile.interactors.get_self_card import GetSelfCardInteractor
from app.application.profile.interactors.get_user_card import GetUserCardInteractor
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor


class ProfileInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetProfileInteractor],
        WithParents[GetSelfCardInteractor],
        WithParents[GetUserCardInteractor],
        WithParents[UpsertProfileInteractor],
    )


providers = [
    ProfileInteractorProvider(),
]
