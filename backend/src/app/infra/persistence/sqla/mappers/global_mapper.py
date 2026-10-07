from typing import Any, cast

from app.domain.common.entity import Entity
from app.infra.persistence.sqla.mappers.access_token_mapper import AccessTokenMapper
from app.infra.persistence.sqla.mappers.audit_event_mapper import AuditEventMapper
from app.infra.persistence.sqla.mappers.auth_identity_mapper import AuthIdentityMapper
from app.infra.persistence.sqla.mappers.chat_mapper import ChatMapper, MessageMapper
from app.infra.persistence.sqla.mappers.dating_profile_mapper import DatingProfileMapper
from app.infra.persistence.sqla.mappers.errors import MapperNotFoundError
from app.infra.persistence.sqla.mappers.interaction_mapper import InteractionMapper
from app.infra.persistence.sqla.mappers.notification_device_mapper import NotificationDeviceMapper
from app.infra.persistence.sqla.mappers.recommendation_mapper import RecommendationMapper
from app.infra.persistence.sqla.mappers.targeting_mapper import TargetingMapper
from app.infra.persistence.sqla.mappers.user_mapper import UserMapper

_Mapper = (
    UserMapper
    | AuthIdentityMapper
    | AccessTokenMapper
    | NotificationDeviceMapper
    | RecommendationMapper
    | TargetingMapper
    | DatingProfileMapper
    | ChatMapper
    | MessageMapper
    | InteractionMapper
    | AuditEventMapper
)


class GlobalDataMapper:
    def __init__(
        self,
        user_mapper: UserMapper,
        auth_identity_mapper: AuthIdentityMapper,
        access_token_mapper: AccessTokenMapper,
        notification_device_mapper: NotificationDeviceMapper,
        recommendation_mapper: RecommendationMapper,
        targeting_mapper: TargetingMapper,
        dating_profile_mapper: DatingProfileMapper,
        chat_mapper: ChatMapper,
        message_mapper: MessageMapper,
        interaction_mapper: InteractionMapper,
        audit_event_mapper: AuditEventMapper,
    ) -> None:
        mappers: list[_Mapper] = [
            user_mapper,
            auth_identity_mapper,
            access_token_mapper,
            notification_device_mapper,
            recommendation_mapper,
            targeting_mapper,
            dating_profile_mapper,
            chat_mapper,
            message_mapper,
            interaction_mapper,
            audit_event_mapper,
        ]
        self._registry: dict[type[Entity[Any]], _Mapper] = {m.entity_type: m for m in mappers}

    def to_rows(self, entity: Entity[Any]) -> list[Any]:
        entity_type = type(entity)
        mapper = self._registry.get(entity_type)
        if mapper is None:
            raise MapperNotFoundError(entity_type)
        rows = mapper.to_rows(cast("Any", entity))
        return list(rows)
