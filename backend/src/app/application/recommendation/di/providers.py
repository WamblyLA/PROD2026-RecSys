from dishka import BaseScope, Provider, Scope, provide

from app.application.recommendation.interactors.get_recommendations import GetRecommendationsInteractor


class RecommendationProviderProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    get_recommendations_interactor = provide(GetRecommendationsInteractor, scope=Scope.REQUEST)


providers = [
    RecommendationProviderProvider(),
]
