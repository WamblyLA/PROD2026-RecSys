from datetime import date
from typing import cast

from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.chat.interactors.get_chat_messages import GetChatMessagesInteractor
from app.application.chat.interactors.get_my_chats import GetMyChatsInteractor
from app.application.chat.interactors.send_chat_message import SendChatMessageInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.application.interaction.interactors.create_interaction import (
    CreateInteractionInteractor,
)
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.chat.entity import ChatId
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.domain.user.value_objects import Gender
from tests.integration.di.identity_provider import MockIdentityProvider  # noqa: TC001


async def _setup_match_and_chat(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> tuple[UserId, UserId]:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email1 = f"chat_a_{test_run_suffix}@test.local"
    email2 = f"chat_b_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    upsert_profile = await test_container.get(UpsertProfileInteractor)
    upsert_dating = await test_container.get(UpsertDatingProfileInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)
    create_interaction = await test_container.get(CreateInteractionInteractor)

    r1 = await sign_up.sign_up_email(email1, password)
    r2 = await sign_up.sign_up_email(email2, password)
    user_a = await user_gateway.load_with_id(r1.user_id)
    user_b = await user_gateway.load_with_id(r2.user_id)
    assert user_a is not None
    assert user_b is not None

    # Оба пользователя получают профиль и dating-профиль.
    for user in (user_a, user_b):
        id_provider.set_user(user)
        await upsert_profile.execute(
            first_name="Chat",
            last_name="User",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            region=None,
            avatar_url=None,
        )
        await upsert_dating.execute(photos=["https://example.com/chat.jpg"])

    # Взаимные лайки по рекомендациям → создаётся чат.
    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    rec_to_b = next((r for r in recs_a.items if r.candidate_user_id == str(user_b.id)), None)
    assert rec_to_b is not None
    await create_interaction.execute(
        candidate_user_id=user_b.id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_b.ml_recommendation_id,
    )

    id_provider.set_user(user_b)
    recs_b = await get_recs.execute()
    rec_to_a = next((r for r in recs_b.items if r.candidate_user_id == str(user_a.id)), None)
    assert rec_to_a is not None
    await create_interaction.execute(
        candidate_user_id=user_a.id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_a.ml_recommendation_id,
    )

    return user_a.id, user_b.id


async def test_chat_flow_between_matched_users(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_match_and_chat(
        test_container,
        test_identity_provider,
        test_run_suffix,
    )

    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    get_my_chats = await test_container.get(GetMyChatsInteractor)
    get_chat_messages = await test_container.get(GetChatMessagesInteractor)
    send_chat_message = await test_container.get(SendChatMessageInteractor)

    # Пользователь A видит чат с B.
    id_provider.set_user(user_a)
    chats_a = await get_my_chats.execute()
    assert len(chats_a.items) == 1
    chat_item = chats_a.items[0]
    assert chat_item.other_user_id == user_b_id

    chat_id = ChatId(chat_item.chat_id)

    # История сообщений изначально пуста.
    messages_before = await get_chat_messages.execute(chat_id=chat_id, limit=50)
    assert messages_before.items == []

    # A отправляет сообщение B.
    text = "Hello from A to B"
    message_item = await send_chat_message.execute(chat_id=chat_id, text=text)
    assert message_item.chat_id == chat_id
    assert message_item.sender_user_id == user_a_id
    assert message_item.text == text

    # История содержит отправленное сообщение.
    messages_after = await get_chat_messages.execute(chat_id=chat_id, limit=50)
    assert len(messages_after.items) == 1
    stored = messages_after.items[0]
    assert stored.message_id == message_item.message_id
    assert stored.chat_id == chat_id
    assert stored.sender_user_id == user_a_id
    assert stored.text == text
