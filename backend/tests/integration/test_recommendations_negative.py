from typing import TYPE_CHECKING, cast

import pytest
from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.common.identity_provider import IdentityProvider
from app.application.profile.errors import ProfileNotFoundError
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.user.data_gateway import UserDataGateway

if TYPE_CHECKING:
    from tests.integration.di.identity_provider import MockIdentityProvider


async def test_get_recommendations_without_ready_dating_profile_raises(
    test_container: AsyncContainer,
    test_identity_provider: IdentityProvider,
    test_run_suffix: str,
) -> None:
    id_provider = cast("MockIdentityProvider", test_identity_provider)
    email = f"user_{test_run_suffix}@test.local"
    password = "test-password-123"  # noqa: S105

    sign_up = await test_container.get(SignUpInteractor)
    user_gateway = await test_container.get(UserDataGateway)
    response = await sign_up.sign_up_email(email, password)
    user = await user_gateway.load_with_id(response.user_id)
    assert user is not None
    id_provider.set_user(user)

    get_recs = await test_container.get(GetRecommendationsInteractor)
    with pytest.raises(ProfileNotFoundError):
        await get_recs.execute()
