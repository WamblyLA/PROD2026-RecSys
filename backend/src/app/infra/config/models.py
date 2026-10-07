from pydantic import BaseModel, ConfigDict, Field


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class ServerConfigModel(BaseConfigModel):
    workers: int = Field(default=1, ge=1, alias="SERVER_WORKERS")
    host: str = Field(default="0.0.0.0", alias="SERVER_HOST")  # noqa: S104
    port: int = Field(default=8080, ge=1, le=65535, alias="SERVER_PORT")


class PostgresConfigModel(BaseConfigModel):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, ge=1, le=65535, alias="POSTGRES_PORT")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="", alias="POSTGRES_PASSWORD")
    db: str = Field(default="app", alias="POSTGRES_DB")


class AccessTokenConfigModel(BaseConfigModel):
    crypto_key: str = Field(default="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", alias="ACCESS_TOKEN_CRYPTO_KEY")
    expires_in_seconds: int = Field(default=86400, ge=1, alias="ACCESS_TOKEN_EXPIRES_IN_SECONDS")


class YandexOAuthConfigModel(BaseConfigModel):
    client_id: str = Field(default="", alias="YANDEX_OAUTH_CLIENT_ID")
    client_secret: str = Field(default="", alias="YANDEX_OAUTH_CLIENT_SECRET")


class OpentelemetryConfigModel(BaseConfigModel):
    traces_exporter: str = Field(default="otlp", alias="OTEL_TRACES_EXPORTER")
    exporter_otlp_endpoint: str = Field(default="http://localhost:4317", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    service_name: str = Field(default="app", alias="OTEL_SERVICE_NAME")


class FirebaseConfigModel(BaseConfigModel):
    certificate_path: str = Field(default="", alias="FIREBASE_CERTIFICATE_PATH")


class MlConfigModel(BaseConfigModel):
    recommendation_provider: str = Field(default="mock", alias="ML_RECOMMENDATION_PROVIDER")
    base_url: str = Field(default="", alias="ML_BASE_URL")
    photo_moderation_provider: str = Field(default="mock", alias="ML_PHOTO_MODERATION_PROVIDER")


class S3ConfigModel(BaseConfigModel):
    endpoint_url: str = Field(default="", alias="S3_ENDPOINT_URL")
    region: str = Field(default="ru-central1", alias="S3_REGION")
    bucket: str = Field(default="", alias="S3_BUCKET")
    access_key_id: str = Field(default="", alias="S3_ACCESS_KEY_ID")
    secret_access_key: str = Field(default="", alias="S3_SECRET_ACCESS_KEY")
    public_base_url: str = Field(default="", alias="S3_PUBLIC_BASE_URL")
