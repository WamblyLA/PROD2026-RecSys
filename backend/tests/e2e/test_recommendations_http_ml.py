from datetime import date
from typing import cast

from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.user.data_gateway import UserDataGateway
from app.domain.user.value_objects import Gender
from tests.integration.di.identity_provider import MockIdentityProvider  # noqa: TC001


async def test_recommendations_with_http_ml_provider_for_user_absent_in_dataset_e2e(
    ml_http_container: AsyncContainer,
    ml_http_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", ml_http_identity_provider)
    email1 = f"http_ml_user1_{test_run_suffix}@test.local"
    email2 = f"http_ml_user2_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await ml_http_container.get(SignUpInteractor)
    user_gateway = await ml_http_container.get(UserDataGateway)
    response1 = await sign_up.sign_up_email(email1, password)
    await sign_up.sign_up_email(email2, password)

    user = await user_gateway.load_with_id(response1.user_id)
    assert user is not None
    id_provider.set_user(user)

    upsert_profile = await ml_http_container.get(UpsertProfileInteractor)
    await upsert_profile.execute(
        first_name="Http",
        last_name="Ml",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        region=None,
        avatar_url=None,
    )

    user_with_profile = await user_gateway.load_with_id(user.id)
    assert user_with_profile is not None
    assert user_with_profile.profile is not None
    id_provider.set_user(user_with_profile)

    upsert_dating = await ml_http_container.get(UpsertDatingProfileInteractor)
    await upsert_dating.execute(photos=["https://example.com/http-ml-photo1.jpg"])

    get_recommendations = await ml_http_container.get(GetRecommendationsInteractor)
    result = await get_recommendations.execute()
    assert isinstance(result.items, list)
    for item in result.items:
        assert item.user_id == str(user.id)
        assert item.ml_recommendation_id
        assert item.candidate_user_id
        assert item.reasons
