from datetime import date
from typing import cast

from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.application.interaction.interactors.create_interaction import (
    CreateInteractionInteractor,
)
from app.application.match.interactors.get_my_matches import GetMyMatchesInteractor
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.interaction.value_objects import InteractionType
from app.domain.user.entity import UserId
from app.domain.user.value_objects import Gender
from tests.integration.di.identity_provider import MockIdentityProvider  # noqa: TC001


async def _setup_two_users_with_profiles_and_recommendations(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> tuple[UserId, UserId]:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email1 = f"match_a_{test_run_suffix}@test.local"
    email2 = f"match_b_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    upsert_profile = await test_container.get(UpsertProfileInteractor)
    upsert_dating = await test_container.get(UpsertDatingProfileInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)

    r1 = await sign_up.sign_up_email(email1, password)
    r2 = await sign_up.sign_up_email(email2, password)
    user_a = await user_gateway.load_with_id(r1.user_id)
    user_b = await user_gateway.load_with_id(r2.user_id)
    assert user_a is not None
    assert user_b is not None

    for user in (user_a, user_b):
        id_provider.set_user(user)
        await upsert_profile.execute(
            first_name="U",
            last_name="X",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            region=None,
            avatar_url=None,
        )
        await upsert_dating.execute(photos=["https://example.com/p.jpg"])
    id_provider.set_user(user_a)
    await get_recs.execute()
    id_provider.set_user(user_b)
    await get_recs.execute()
    return user_a.id, user_b.id


async def test_mutual_like_returns_match(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)
    get_matches = await test_container.get(GetMyMatchesInteractor)

    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    rec_to_b = next((r for r in recs_a.items if r.candidate_user_id == str(user_b_id)), None)
    assert rec_to_b is not None
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_b.ml_recommendation_id,
    )

    id_provider.set_user(user_b)
    recs_b = await get_recs.execute()
    rec_to_a = next((r for r in recs_b.items if r.candidate_user_id == str(user_a_id)), None)
    assert rec_to_a is not None
    await create_interaction.execute(
        candidate_user_id=user_a_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_a.ml_recommendation_id,
    )

    id_provider.set_user(user_a)
    matches_a = await get_matches.execute()
    assert len(matches_a.items) == 1
    assert matches_a.items[0].candidate_user_id == str(user_b_id)

    id_provider.set_user(user_b)
    matches_b = await get_matches.execute()
    assert len(matches_b.items) == 1
    assert matches_b.items[0].candidate_user_id == str(user_a_id)


async def test_one_sided_like_returns_no_match(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)
    get_matches = await test_container.get(GetMyMatchesInteractor)

    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    rec_to_b = next((r for r in recs_a.items if r.candidate_user_id == str(user_b_id)), None)
    assert rec_to_b is not None
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_b.ml_recommendation_id,
    )

    id_provider.set_user(user_a)
    matches_a = await get_matches.execute()
    assert len(matches_a.items) == 0


async def test_dislike_removes_match(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)
    get_matches = await test_container.get(GetMyMatchesInteractor)

    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    rec_to_b = next((r for r in recs_a.items if r.candidate_user_id == str(user_b_id)), None)
    assert rec_to_b is not None
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_b.ml_recommendation_id,
    )

    id_provider.set_user(user_b)
    recs_b = await get_recs.execute()
    rec_to_a = next((r for r in recs_b.items if r.candidate_user_id == str(user_a_id)), None)
    assert rec_to_a is not None
    await create_interaction.execute(
        candidate_user_id=user_a_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_a.ml_recommendation_id,
    )

    id_provider.set_user(user_a)
    matches_before = await get_matches.execute()
    assert len(matches_before.items) == 1

    id_provider.set_user(user_b)
    recs_b2 = await get_recs.execute()
    rec_to_a2 = next((r for r in recs_b2.items if r.candidate_user_id == str(user_a_id)), None)
    assert rec_to_a2 is not None
    await create_interaction.execute(
        candidate_user_id=user_a_id,
        action=InteractionType.DISLIKE,
        ml_recommendation_id=rec_to_a2.ml_recommendation_id,
    )

    id_provider.set_user(user_a)
    matches_after_a = await get_matches.execute()
    assert len(matches_after_a.items) == 0

    id_provider.set_user(user_b)
    matches_after_b = await get_matches.execute()
    assert len(matches_after_b.items) == 0


async def test_block_removes_match(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)
    get_matches = await test_container.get(GetMyMatchesInteractor)

    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    rec_to_b = next((r for r in recs_a.items if r.candidate_user_id == str(user_b_id)), None)
    assert rec_to_b is not None
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_b.ml_recommendation_id,
    )
    id_provider.set_user(user_b)
    recs_b = await get_recs.execute()
    rec_to_a = next((r for r in recs_b.items if r.candidate_user_id == str(user_a_id)), None)
    assert rec_to_a is not None
    await create_interaction.execute(
        candidate_user_id=user_a_id,
        action=InteractionType.LIKE,
        ml_recommendation_id=rec_to_a.ml_recommendation_id,
    )

    id_provider.set_user(user_a)
    matches_before = await get_matches.execute()
    assert len(matches_before.items) == 1

    id_provider.set_user(user_a)
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.BLOCK,
        ml_recommendation_id=None,
    )

    id_provider.set_user(user_a)
    matches_after_a = await get_matches.execute()
    assert len(matches_after_a.items) == 0
    id_provider.set_user(user_b)
    matches_after_b = await get_matches.execute()
    assert len(matches_after_b.items) == 0


async def test_blocked_user_excluded_from_recommendations(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)

    id_provider.set_user(user_a)
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.BLOCK,
        ml_recommendation_id=None,
    )

    id_provider.set_user(user_a)
    recs_a = await get_recs.execute()
    candidate_ids_a = [r.candidate_user_id for r in recs_a.items]
    assert str(user_b_id) not in candidate_ids_a

    id_provider.set_user(user_b)
    recs_b = await get_recs.execute()
    candidate_ids_b = [r.candidate_user_id for r in recs_b.items]
    assert str(user_a_id) not in candidate_ids_b


async def test_unblock_removes_block_state(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    user_a_id, user_b_id = await _setup_two_users_with_profiles_and_recommendations(
        test_container, test_identity_provider, test_run_suffix
    )
    user_gateway = await test_container.get(UserDataGateway)
    user_a = await user_gateway.load_with_id(user_a_id)
    user_b = await user_gateway.load_with_id(user_b_id)
    assert user_a is not None
    assert user_b is not None

    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_recs = await test_container.get(GetRecommendationsInteractor)

    id_provider.set_user(user_a)
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.BLOCK,
        ml_recommendation_id=None,
    )
    id_provider.set_user(user_a)
    recs_after_block = await get_recs.execute()
    assert str(user_b_id) not in [r.candidate_user_id for r in recs_after_block.items]

    id_provider.set_user(user_a)
    await create_interaction.execute(
        candidate_user_id=user_b_id,
        action=InteractionType.UNBLOCK,
        ml_recommendation_id=None,
    )
    id_provider.set_user(user_a)
    recs_after_unblock = await get_recs.execute()
    assert str(user_b_id) in [r.candidate_user_id for r in recs_after_unblock.items]
