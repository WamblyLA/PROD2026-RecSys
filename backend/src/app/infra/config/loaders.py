from adaptix import Retort

from app.infra.config.models import (
    AccessTokenConfigModel,
    FirebaseConfigModel,
    MlConfigModel,
    OpentelemetryConfigModel,
    PostgresConfigModel,
    S3ConfigModel,
    ServerConfigModel,
    YandexOAuthConfigModel,
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

retort = Retort()


class BaseEnvLoader:
    def __init__(self, source: EnvSource) -> None:
        self._source = source


class EnvServerConfigLoader(BaseEnvLoader):
    def load(self) -> ServerConfig:
        raw_data = self._source.get_present_values(["SERVER_WORKERS", "SERVER_HOST", "SERVER_PORT"])
        validated = ServerConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, ServerConfig)


class EnvPostgresConfigLoader(BaseEnvLoader):
    def load(self) -> PostgresConfig:
        raw_data = self._source.get_present_values(
            ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
        )
        validated = PostgresConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, PostgresConfig)


class EnvAccessTokenConfigLoader(BaseEnvLoader):
    def load(self) -> AccessTokenConfig:
        raw_data = self._source.get_present_values(["ACCESS_TOKEN_CRYPTO_KEY", "ACCESS_TOKEN_EXPIRES_IN_SECONDS"])
        validated = AccessTokenConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, AccessTokenConfig)


class EnvYandexOAuthConfigLoader(BaseEnvLoader):
    def load(self) -> YandexOAuthConfig:
        raw_data = self._source.get_present_values(["YANDEX_OAUTH_CLIENT_ID", "YANDEX_OAUTH_CLIENT_SECRET"])
        validated = YandexOAuthConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, YandexOAuthConfig)


class EnvOpentelemetryConfigLoader(BaseEnvLoader):
    def load(self) -> OpentelemetryConfig:
        raw_data = self._source.get_present_values(
            ["OTEL_TRACES_EXPORTER", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_SERVICE_NAME"]
        )
        validated = OpentelemetryConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, OpentelemetryConfig)


class EnvFirebaseConfigLoader(BaseEnvLoader):
    def load(self) -> FirebaseConfig:
        raw_data = self._source.get_present_values(["FIREBASE_CERTIFICATE_PATH"])
        validated = FirebaseConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, FirebaseConfig)


class EnvMlConfigLoader(BaseEnvLoader):
    def load(self) -> MlConfig:
        raw_data = self._source.get_present_values(
            ["ML_RECOMMENDATION_PROVIDER", "ML_BASE_URL", "ML_PHOTO_MODERATION_PROVIDER"]
        )
        validated = MlConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, MlConfig)


class EnvS3ConfigLoader(BaseEnvLoader):
    def load(self) -> S3Config:
        raw_data = self._source.get_present_values(
            [
                "S3_ENDPOINT_URL",
                "S3_REGION",
                "S3_BUCKET",
                "S3_ACCESS_KEY_ID",
                "S3_SECRET_ACCESS_KEY",
                "S3_PUBLIC_BASE_URL",
            ]
        )
        validated = S3ConfigModel.model_validate(raw_data).model_dump()

        return retort.load(validated, S3Config)
