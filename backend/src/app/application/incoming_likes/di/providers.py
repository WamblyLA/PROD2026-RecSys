from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.incoming_likes.interactors.get_my_incoming_likes import (
    GetMyIncomingLikesInteractor,
)


class IncomingLikesInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetMyIncomingLikesInteractor],
    )


providers = [
    IncomingLikesInteractorProvider(),
]
