from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.targeting.interactors.get_my_targeting import GetMyTargetingInteractor
from app.application.targeting.interactors.upsert_my_targeting import UpsertMyTargetingInteractor


class TargetingInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetMyTargetingInteractor],
        WithParents[UpsertMyTargetingInteractor],
    )


providers = [
    TargetingInteractorProvider(),
]
