from dishka import BaseScope, Provider, Scope, provide, provide_all

from app.infra.config.loaders import (
    EnvAccessTokenConfigLoader,
    EnvFirebaseConfigLoader,
    EnvMlConfigLoader,
    EnvOpentelemetryConfigLoader,
    EnvPostgresConfigLoader,
    EnvS3ConfigLoader,
    EnvServerConfigLoader,
    EnvYandexOAuthConfigLoader,
)
from app.infra.config.sources import EnvSource
from app.presentation.api.config.models import (
    AccessTokenConfig,
    FirebaseConfig,
    MlConfig,
    OpentelemetryConfig,
    PostgresConfig,
    S3Config,
    ServerConfig,
    YandexOAuthConfig,
)


class SourcesProvider(Provider):
    scope: BaseScope | None = Scope.APP

    sources = provide_all(
        EnvSource,
    )


class ConfigProvider(Provider):
    scope: BaseScope | None = Scope.APP

    loaders = provide_all(
        EnvServerConfigLoader,
        EnvPostgresConfigLoader,
        EnvAccessTokenConfigLoader,
        EnvYandexOAuthConfigLoader,
        EnvOpentelemetryConfigLoader,
        EnvFirebaseConfigLoader,
        EnvMlConfigLoader,
        EnvS3ConfigLoader,
    )

    @provide
    def env_server_config(self, loader: EnvServerConfigLoader) -> ServerConfig:
        return loader.load()

    @provide
    def env_postgres_config(self, loader: EnvPostgresConfigLoader) -> PostgresConfig:
        return loader.load()

    @provide
    def env_access_token_config(self, loader: EnvAccessTokenConfigLoader) -> AccessTokenConfig:
        return loader.load()

    @provide
    def env_yandex_oauth_config(self, loader: EnvYandexOAuthConfigLoader) -> YandexOAuthConfig:
        return loader.load()

    @provide
    def env_opentelemetry_config(self, loader: EnvOpentelemetryConfigLoader) -> OpentelemetryConfig:
        return loader.load()

    @provide
    def env_firebase_config(self, loader: EnvFirebaseConfigLoader) -> FirebaseConfig:
        return loader.load()

    @provide
    def env_ml_config(self, loader: EnvMlConfigLoader) -> MlConfig:
        return loader.load()

    @provide
    def env_s3_config(self, loader: EnvS3ConfigLoader) -> S3Config:
        return loader.load()


providers = [
    SourcesProvider(),
    ConfigProvider(),
]
