from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    workers: int


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    user: str
    password: str
    db: str


@dataclass(frozen=True)
class AccessTokenConfig:
    crypto_key: str
    expires_in_seconds: int


@dataclass(frozen=True)
class YandexOAuthConfig:
    client_id: str
    client_secret: str


@dataclass(frozen=True)
class OpentelemetryConfig:
    traces_exporter: str
    exporter_otlp_endpoint: str
    service_name: str


@dataclass(frozen=True)
class FirebaseConfig:
    certificate_path: str


@dataclass(frozen=True)
class MlConfig:
    recommendation_provider: str
    base_url: str
    photo_moderation_provider: str


@dataclass(frozen=True)
class S3Config:
    endpoint_url: str
    region: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    public_base_url: str
