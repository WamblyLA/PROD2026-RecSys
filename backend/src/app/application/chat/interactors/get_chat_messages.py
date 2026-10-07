from app.application.chat.data_gateway import ChatDataGateway
from app.application.chat.dto import ChatMessageItem, ChatMessagesResult
from app.application.chat.errors import ChatAccessDeniedError, ChatNotFoundError
from app.application.common.identity_provider import IdentityProvider
from app.application.common.interactor import interactor
from app.domain.chat.entity import ChatId, MessageId


@interactor
class GetChatMessagesInteractor:
    identity_provider: IdentityProvider
    chat_data_gateway: ChatDataGateway

    async def execute(
        self,
        *,
        chat_id: ChatId,
        limit: int,
        before_message_id: MessageId | None = None,
    ) -> ChatMessagesResult:
        if limit <= 0:
            limit = 50
        limit = min(limit, 200)

        user = await self.identity_provider.get_current_user()
        chat = await self.chat_data_gateway.load_chat_by_id(chat_id)
        if chat is None:
            raise ChatNotFoundError
        if user.id not in (chat.user_a_id, chat.user_b_id):
            raise ChatAccessDeniedError

        messages = await self.chat_data_gateway.list_messages(
            chat_id=chat_id,
            limit=limit,
            before_message_id=before_message_id,
        )
        items = [
            ChatMessageItem(
                message_id=m.id,
                chat_id=m.chat_id,
                sender_user_id=m.sender_user_id,
                text=m.text,
                created_at=m.created_at,
            )
            for m in messages
        ]
        return ChatMessagesResult(items=items)
