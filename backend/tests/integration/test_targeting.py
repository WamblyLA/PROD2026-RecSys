from datetime import UTC, date, datetime
from typing import cast

import pytest
from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.targeting.errors import TargetingValidationError
from app.application.targeting.interactors.get_my_targeting import GetMyTargetingInteractor
from app.application.targeting.interactors.upsert_my_targeting import UpsertMyTargetingInteractor
from app.application.user.data_gateway import UserDataGateway
from app.domain.user.value_objects import Gender
from tests.integration.di.identity_provider import MockIdentityProvider  # noqa: TC001


async def test_upsert_then_get_targeting(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email = f"targeting_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    response = await sign_up.sign_up_email(email, password)
    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    upsert_profile = await test_container.get(UpsertProfileInteractor)
    await upsert_profile.execute(
        first_name="T",
        last_name="U",
        birth_date=date(1995, 5, 5),
        gender=Gender.MALE,
        region="Moscow",
        avatar_url=None,
    )

    upsert_targeting = await test_container.get(UpsertMyTargetingInteractor)
    await upsert_targeting.execute(
        region="Moscow",
        gender_target="female",
        age_from=20,
        age_to=35,
    )

    get_targeting = await test_container.get(GetMyTargetingInteractor)
    result = await get_targeting.execute()
    assert result.rules.region == "Moscow"
    assert result.rules.gender_target.value == "female"
    assert result.rules.age_from == 20
    assert result.rules.age_to == 35


async def test_get_targeting_without_upsert_returns_default(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email = f"notarget_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    response = await sign_up.sign_up_email(email, password)
    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    get_targeting = await test_container.get(GetMyTargetingInteractor)
    result = await get_targeting.execute()
    assert result.rules.region is None
    assert result.rules.gender_target.value == "both"
    assert result.rules.age_from == 0
    assert result.rules.age_to == 2


async def test_get_targeting_without_upsert_with_profile_age_based_defaults(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email = f"notarget_profile_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105
    birth_date = date(1999, 5, 15)

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    response = await sign_up.sign_up_email(email, password)
    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    upsert_profile = await test_container.get(UpsertProfileInteractor)
    await upsert_profile.execute(
        first_name="T",
        last_name="U",
        birth_date=birth_date,
        gender=Gender.MALE,
        region="Moscow",
        avatar_url=None,
    )

    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    today = datetime.now(tz=UTC).date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    get_targeting = await test_container.get(GetMyTargetingInteractor)
    result = await get_targeting.execute()
    assert result.rules.region == "Moscow"
    assert result.rules.gender_target.value == "both"
    assert result.rules.age_from == max(0, age - 2)
    assert result.rules.age_to == age + 2


async def test_upsert_targeting_invalid_age_range_raises(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email = f"invalid_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    response = await sign_up.sign_up_email(email, password)
    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    upsert_targeting = await test_container.get(UpsertMyTargetingInteractor)
    with pytest.raises(TargetingValidationError):
        await upsert_targeting.execute(
            region=None,
            gender_target="both",
            age_from=25,
            age_to=20,
        )
