from dishka import AsyncContainer

from app.application.auth_identity.interactors.sign_in import SignInInteractor
from app.application.auth_identity.interactors.sign_up import SignUpInteractor
from app.application.dating_profile.interactors.get_dating_profile import (
    GetDatingProfileInteractor,
)
from app.application.dating_profile.interactors.set_trait_visibility import (
    SetTraitVisibilityInteractor,
)
from app.application.dating_profile.interactors.upsert_dating_profile import (
    UpsertDatingProfileInteractor,
)
from app.application.interaction.interactors.create_interaction import (
    CreateInteractionInteractor,
)
from app.application.match.interactors.get_my_matches import GetMyMatchesInteractor
from app.application.notification_device.interactors.register_device import (
    RegisterNotificationDeviceInteractor,
)
from app.application.notification_device.interactors.send_notification import (
    SendNotificationInteractor,
)
from app.application.profile.interactors.get_profile import GetProfileInteractor
from app.application.profile.interactors.get_self_card import GetSelfCardInteractor
from app.application.profile.interactors.get_user_card import GetUserCardInteractor
from app.application.profile.interactors.upsert_profile import UpsertProfileInteractor
from app.application.recommendation.interactors.get_recommendations import (
    GetRecommendationsInteractor,
)
from app.application.targeting.interactors.get_my_targeting import GetMyTargetingInteractor
from app.application.targeting.interactors.upsert_my_targeting import UpsertMyTargetingInteractor


async def test_all_interactors_resolve(test_container: AsyncContainer) -> None:
    sign_up = await test_container.get(SignUpInteractor)
    sign_in = await test_container.get(SignInInteractor)
    get_profile = await test_container.get(GetProfileInteractor)
    get_self_card = await test_container.get(GetSelfCardInteractor)
    get_user_card = await test_container.get(GetUserCardInteractor)
    upsert_profile = await test_container.get(UpsertProfileInteractor)
    get_dating_profile = await test_container.get(GetDatingProfileInteractor)
    upsert_dating_profile = await test_container.get(UpsertDatingProfileInteractor)
    set_trait_visibility = await test_container.get(SetTraitVisibilityInteractor)
    get_recommendations = await test_container.get(GetRecommendationsInteractor)
    get_my_targeting = await test_container.get(GetMyTargetingInteractor)
    upsert_my_targeting = await test_container.get(UpsertMyTargetingInteractor)
    create_interaction = await test_container.get(CreateInteractionInteractor)
    get_my_matches = await test_container.get(GetMyMatchesInteractor)
    send_notification = await test_container.get(SendNotificationInteractor)
    register_device = await test_container.get(RegisterNotificationDeviceInteractor)

    assert sign_up is not None
    assert sign_in is not None
    assert get_profile is not None
    assert get_self_card is not None
    assert get_user_card is not None
    assert upsert_profile is not None
    assert get_dating_profile is not None
    assert upsert_dating_profile is not None
    assert set_trait_visibility is not None
    assert get_recommendations is not None
    assert get_my_targeting is not None
    assert upsert_my_targeting is not None
    assert create_interaction is not None
    assert get_my_matches is not None
    assert send_notification is not None
    assert register_device is not None
