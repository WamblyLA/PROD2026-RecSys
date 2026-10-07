from dishka import BaseScope, Provider, Scope, provide

from app.application.chat.interactors.get_chat_messages import GetChatMessagesInteractor
from app.application.chat.interactors.get_my_chats import GetMyChatsInteractor
from app.application.chat.interactors.send_chat_message import SendChatMessageInteractor


class ChatInteractorProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    get_my_chats = provide(GetMyChatsInteractor, scope=Scope.REQUEST)
    get_chat_messages = provide(GetChatMessagesInteractor, scope=Scope.REQUEST)
    send_chat_message = provide(SendChatMessageInteractor, scope=Scope.REQUEST)


providers = [
    ChatInteractorProvider(),
]
