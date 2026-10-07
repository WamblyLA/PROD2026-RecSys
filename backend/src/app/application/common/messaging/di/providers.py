from dishka import BaseScope, Provider, Scope, provide

from app.application.common.messaging.in_memory import InMemoryMessagingService
from app.application.common.messaging.service import MessagingService


class MessagingProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide(scope=Scope.APP)
    def messaging_service(self) -> MessagingService:
        return InMemoryMessagingService()


providers = [
    MessagingProvider(),
]
