from dishka import BaseScope, Provider, Scope, WithParents, provide_all

from app.application.auth_identity.interactors.sign_in import SignInInteractor
from app.application.auth_identity.interactors.sign_up import SignUpInteractor


class AuthIdentityInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    provides = provide_all(
        WithParents[SignUpInteractor],
        WithParents[SignInInteractor],
    )


providers = [
    AuthIdentityInteractorProvider(),
]
