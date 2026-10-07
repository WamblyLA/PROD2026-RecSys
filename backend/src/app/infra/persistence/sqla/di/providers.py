from collections.abc import AsyncIterable
from urllib.parse import quote_plus

from dishka import BaseScope, Provider, Scope, WithParents, provide, provide_all
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.infra.persistence.sqla.bootstrapper import SqlaPersistenceBootstrapper
from app.infra.persistence.sqla.data_gateways.access_token import DefaultAccessTokenDataGateway
from app.infra.persistence.sqla.data_gateways.auth_identity import DefaultAuthIdentityDataGateway
from app.infra.persistence.sqla.data_gateways.blocked_pairs import DefaultBlockedPairsGateway
from app.infra.persistence.sqla.data_gateways.chat import DefaultChatDataGateway
from app.infra.persistence.sqla.data_gateways.dating_profile import DefaultDatingProfileDataGateway
from app.infra.persistence.sqla.data_gateways.incoming_likes import DefaultIncomingLikesDataGateway
from app.infra.persistence.sqla.data_gateways.match import DefaultMatchDataGateway
from app.infra.persistence.sqla.data_gateways.notification_device import DefaultNotificationDeviceDataGateway
from app.infra.persistence.sqla.data_gateways.recommendation import DefaultRecommendationDataGateway
from app.infra.persistence.sqla.data_gateways.targeting import DefaultTargetingDataGateway
from app.infra.persistence.sqla.data_gateways.user import DefaultUserDataGateway
from app.infra.persistence.sqla.mappers import GlobalDataMapper
from app.infra.persistence.sqla.mappers.access_token_mapper import AccessTokenMapper
from app.infra.persistence.sqla.mappers.audit_event_mapper import AuditEventMapper
from app.infra.persistence.sqla.mappers.auth_identity_mapper import AuthIdentityMapper
from app.infra.persistence.sqla.mappers.chat_mapper import ChatMapper, MessageMapper
from app.infra.persistence.sqla.mappers.dating_profile_mapper import DatingProfileMapper
from app.infra.persistence.sqla.mappers.interaction_mapper import InteractionMapper
from app.infra.persistence.sqla.mappers.notification_device_mapper import NotificationDeviceMapper
from app.infra.persistence.sqla.mappers.recommendation_mapper import RecommendationMapper
from app.infra.persistence.sqla.mappers.targeting_mapper import TargetingMapper
from app.infra.persistence.sqla.mappers.user_mapper import UserMapper
from app.infra.persistence.sqla.readiness import SqlaReadinessChecker
from app.infra.persistence.sqla.uow import DefaultUnitOfWork
from app.presentation.api.bootstrap.persistence_bootstrapper import PersistenceBootstrapper
from app.presentation.api.bootstrap.readiness_checker import ReadinessChecker
from app.presentation.api.config.models import PostgresConfig


def _build_url(config: PostgresConfig) -> str:
    password = quote_plus(config.password)
    return f"postgresql+psycopg://{config.user}:{password}@{config.host}:{config.port}/{config.db}"


class SqlaProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide(scope=Scope.APP)
    async def engine(self, postgres_config: PostgresConfig) -> AsyncIterable[AsyncEngine]:
        url = _build_url(postgres_config)
        engine = create_async_engine(url)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def async_session(self, engine: AsyncEngine) -> AsyncIterable[AsyncSession]:
        session = AsyncSession(bind=engine, expire_on_commit=False)
        async with session:
            yield session

    persistence_bootstrapper = provide(
        source=SqlaPersistenceBootstrapper,
        provides=PersistenceBootstrapper,
        scope=Scope.APP,
    )
    readiness_checker = provide(
        source=SqlaReadinessChecker,
        provides=ReadinessChecker,
        scope=Scope.APP,
    )


class MapperProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    user_mapper = provide(UserMapper, scope=Scope.REQUEST)
    auth_identity_mapper = provide(AuthIdentityMapper, scope=Scope.REQUEST)
    access_token_mapper = provide(AccessTokenMapper, scope=Scope.REQUEST)
    notification_device_mapper = provide(NotificationDeviceMapper, scope=Scope.REQUEST)
    recommendation_mapper = provide(RecommendationMapper, scope=Scope.REQUEST)
    targeting_mapper = provide(TargetingMapper, scope=Scope.REQUEST)
    dating_profile_mapper = provide(DatingProfileMapper, scope=Scope.REQUEST)
    chat_mapper = provide(ChatMapper, scope=Scope.REQUEST)
    message_mapper = provide(MessageMapper, scope=Scope.REQUEST)
    interaction_mapper = provide(InteractionMapper, scope=Scope.REQUEST)
    audit_event_mapper = provide(AuditEventMapper, scope=Scope.REQUEST)
    global_data_mapper = provide(GlobalDataMapper, scope=Scope.REQUEST)


class DataGatewayProvider(Provider):
    scope: BaseScope | None = Scope.REQUEST

    unit_of_work = provide(WithParents[DefaultUnitOfWork], scope=Scope.REQUEST)
    data_gateways = provide_all(
        WithParents[DefaultUserDataGateway],
        WithParents[DefaultAccessTokenDataGateway],
        WithParents[DefaultAuthIdentityDataGateway],
        WithParents[DefaultDatingProfileDataGateway],
        WithParents[DefaultNotificationDeviceDataGateway],
        WithParents[DefaultRecommendationDataGateway],
        WithParents[DefaultTargetingDataGateway],
        WithParents[DefaultMatchDataGateway],
        WithParents[DefaultBlockedPairsGateway],
        WithParents[DefaultIncomingLikesDataGateway],
        WithParents[DefaultChatDataGateway],
    )


providers = [
    SqlaProvider(),
    MapperProvider(),
    DataGatewayProvider(),
]
