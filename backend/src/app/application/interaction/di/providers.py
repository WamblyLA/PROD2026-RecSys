from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.interaction.interactors.create_interaction import CreateInteractionInteractor


class InteractionInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[CreateInteractionInteractor],
    )


providers = [
    InteractionInteractorProvider(),
]
