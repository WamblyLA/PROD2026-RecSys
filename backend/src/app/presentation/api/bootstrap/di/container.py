from dishka import STRICT_VALIDATION, AsyncContainer, make_async_container
from dishka.integrations.litestar import LitestarProvider

from app.application.auth_identity.di.providers import providers as auth_identity_providers
from app.application.chat.di.providers import providers as chat_providers
from app.application.common.messaging.di.providers import providers as messaging_providers
from app.application.dating_profile.di.providers import providers as dating_profile_providers
from app.application.incoming_likes.di.providers import providers as incoming_likes_providers
from app.application.interaction.di.providers import providers as interaction_providers
from app.application.match.di.providers import providers as match_providers
from app.application.notification_device.di.providers import providers as notification_device_providers
from app.application.preview.di.providers import providers as preview_providers
from app.application.profile.di.providers import providers as profile_providers
from app.application.recommendation.di.providers import providers as recommendation_providers
from app.application.targeting.di.providers import providers as targeting_providers
from app.infra.config.di.providers import providers as config_providers
from app.infra.ml.di.providers import providers as ml_providers
from app.infra.notifications.di.providers import providers as notification_providers
from app.infra.oauth.di.providers import providers as oauth_providers
from app.infra.persistence.sqla.di.providers import providers as sqla_providers
from app.infra.security.di.providers import providers as security_providers
from app.infra.storage.di.providers import providers as storage_providers
from app.presentation.api.bootstrap.di.identity_provider import IdentityProviderProvider


def build_container() -> AsyncContainer:
    return make_async_container(
        LitestarProvider(),
        *config_providers,
        *sqla_providers,
        *security_providers,
        *oauth_providers,
        *ml_providers,
        *storage_providers,
        *auth_identity_providers,
        *messaging_providers,
        *notification_providers,
        IdentityProviderProvider(),
        *notification_device_providers,
        *profile_providers,
        *recommendation_providers,
        *match_providers,
        *incoming_likes_providers,
        *preview_providers,
        *targeting_providers,
        *dating_profile_providers,
        *interaction_providers,
        *chat_providers,
        validation_settings=STRICT_VALIDATION,
    )
