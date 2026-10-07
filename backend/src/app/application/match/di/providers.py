from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.match.interactors.get_my_matches import GetMyMatchesInteractor


class MatchInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetMyMatchesInteractor],
    )


providers = [
    MatchInteractorProvider(),
]
