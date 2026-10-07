from datetime import date
from typing import cast
from uuid import UUID

from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.application.interaction.interactors.create_interaction import (
    CreateInteractionInteractor,
)
from app.application.profile.interactors.get_self_card import GetSelfCardInteractor
from app.application.profile.interactors.get_user_card import GetUserCardInteractor
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.domain.user.value_objects import Gender
from tests.integration.di.identity_provider import MockIdentityProvider  # noqa: TC001


async def test_registration_recommendations_like_flow(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email1 = f"user1_{test_run_suffix}@test.local"
    email2 = f"user2_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)

    response1 = await sign_up.sign_up_email(email1, password)
    await sign_up.sign_up_email(email2, password)

    user_a = await user_gateway.load_with_id(response1.user_id)
    assert user_a is not None
    id_provider.set_user(user_a)

    upsert_profile = await test_container.get(UpsertProfileInteractor)
    await upsert_profile.execute(
        first_name="Test",
        last_name="User",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        region=None,
        avatar_url=None,
    )

    user_a_with_profile = await user_gateway.load_with_id(user_a.id)
    assert user_a_with_profile is not None
    assert user_a_with_profile.profile is not None
    id_provider.set_user(user_a_with_profile)

    upsert_dating = await test_container.get(UpsertDatingProfileInteractor)
    await upsert_dating.execute(photos=["https://example.com/photo1.jpg"])
    get_self_card = await test_container.get(GetSelfCardInteractor)
    self_card = await get_self_card.execute()
    assert self_card.user_id == str(user_a.id)
    assert self_card.profile is not None
    assert self_card.dating_profile is not None

    get_recs = await test_container.get(GetRecommendationsInteractor)
    recs = await get_recs.execute()
    assert len(recs.items) >= 1
    item = recs.items[0]
    assert item.user_id == str(user_a.id)
    assert item.candidate_user_id
    assert item.ml_recommendation_id
    assert item.reasons
    assert item.candidate_card is not None
    assert item.candidate_card.user_id == item.candidate_user_id

    get_user_card = await test_container.get(GetUserCardInteractor)
    candidate_card = await get_user_card.execute(user_id=UserId(UUID(item.candidate_user_id)))
    assert candidate_card.user_id == item.candidate_user_id

    create_interaction = await test_container.get(CreateInteractionInteractor)
    result = await create_interaction.execute(
        candidate_user_id=UserId(UUID(item.candidate_user_id)),
        action=InteractionType.LIKE,
        ml_recommendation_id=item.ml_recommendation_id,
    )
    assert result.action == InteractionType.LIKE
    assert result.candidate_user_id == UserId(UUID(item.candidate_user_id))
    assert result.ml_recommendation_id == item.ml_recommendation_id
