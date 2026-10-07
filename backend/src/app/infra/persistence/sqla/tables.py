from typing import Final

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import registry

from app.domain.audit_event.value_objects import AuditEventType
from app.domain.auth_identity.value_objects import AuthMethod
from app.domain.interaction.value_objects import InteractionType
from app.domain.targeting.value_objects import TargetGender
from app.domain.user.value_objects import Gender
from app.infra.persistence.sqla.rows import (
    AccessTokenRow,
    AuditEventRow,
    AuthIdentityRow,
    ChatRow,
    DatingProfilePhotoRow,
    DatingProfileRow,
    DatingProfileTraitRow,
    InteractionRow,
    MessageRow,
    NotificationDeviceRow,
    ProfileRow,
    RecommendationRow,
    TargetingRow,
    UserRow,
)

meta_data: Final = MetaData()
mapper_registry: Final = registry()

user_table: Final = Table(
    "users",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("deleted_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

profile_table: Final = Table(
    "profiles",
    meta_data,
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("first_name", String, nullable=False),
    Column("last_name", String, nullable=True),
    Column("birth_date", Date, nullable=False),
    Column("gender", Enum(Gender, name="profile_gender"), nullable=False),
    Column("region", String, nullable=True),
    Column("avatar_url", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

auth_identity_table: Final = Table(
    "auth_identities",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("method", Enum(AuthMethod, name="auth_method"), nullable=False),
    Column("identifier", String, nullable=False),
    Column("secret_key", String, nullable=True),
    Column("deleted_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

access_token_table: Final = Table(
    "access_token",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("revoked", Boolean, nullable=False),
    Column("expires_in", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

notification_device_table: Final = Table(
    "notification_devices",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("device_id", String, nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "device_id", name="uq_notification_devices_user_device"),
)

recommendation_table: Final = Table(
    "recommendations",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("ml_recommendation_id", String, nullable=False),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("candidate_user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("reasons", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

targeting_table: Final = Table(
    "targeting",
    meta_data,
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("region", String, nullable=True),
    Column("gender_target", Enum(TargetGender, name="target_gender"), nullable=False),
    Column("age_from", Integer, nullable=False),
    Column("age_to", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

dating_profile_table: Final = Table(
    "dating_profiles",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
)

dating_profile_photo_table: Final = Table(
    "dating_profile_photos",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column(
        "dating_profile_id",
        UUID,
        ForeignKey("dating_profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("url", String, nullable=False),
    Column("position", Integer, nullable=False),
)

dating_profile_trait_table: Final = Table(
    "dating_profile_traits",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column(
        "dating_profile_id",
        UUID,
        ForeignKey("dating_profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("trait_code", String, nullable=False),
    Column("score", Float, nullable=False),
    Column("is_hidden", Boolean, nullable=False),
)

interaction_table: Final = Table(
    "interactions",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("actor_user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("candidate_user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("action", Enum(InteractionType, name="interaction_type"), nullable=False),
    Column("ml_recommendation_id", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
)

chat_table: Final = Table(
    "chats",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("user_a_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("user_b_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
    UniqueConstraint("user_a_id", "user_b_id", name="uq_chats_user_pair"),
)

message_table: Final = Table(
    "messages",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("chat_id", UUID, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
    Column("sender_user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("text", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True)),
)

audit_event_table: Final = Table(
    "audit_events",
    meta_data,
    Column("id", UUID, primary_key=True),
    Column("event_type", Enum(AuditEventType, name="audit_event_type"), nullable=False),
    Column("actor_user_id", UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    Column("target_user_id", UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    Column("ml_recommendation_id", String, nullable=True),
    Column("payload", JSONB, nullable=True),
    Column("sent_to_ml", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
)

mapper_registry.map_imperatively(UserRow, user_table)
mapper_registry.map_imperatively(ProfileRow, profile_table)
mapper_registry.map_imperatively(AuthIdentityRow, auth_identity_table)
mapper_registry.map_imperatively(AccessTokenRow, access_token_table)
mapper_registry.map_imperatively(NotificationDeviceRow, notification_device_table)
mapper_registry.map_imperatively(RecommendationRow, recommendation_table)
mapper_registry.map_imperatively(TargetingRow, targeting_table)
mapper_registry.map_imperatively(DatingProfileRow, dating_profile_table)
mapper_registry.map_imperatively(DatingProfilePhotoRow, dating_profile_photo_table)
mapper_registry.map_imperatively(DatingProfileTraitRow, dating_profile_trait_table)
mapper_registry.map_imperatively(InteractionRow, interaction_table)
mapper_registry.map_imperatively(AuditEventRow, audit_event_table)
mapper_registry.map_imperatively(ChatRow, chat_table)
mapper_registry.map_imperatively(MessageRow, message_table)
