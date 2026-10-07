from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.preview.interactors.get_preview_cards import GetPreviewCardsInteractor


class PreviewInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[GetPreviewCardsInteractor],
    )


providers = [
    PreviewInteractorProvider(),
]
