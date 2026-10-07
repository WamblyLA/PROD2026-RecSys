from collections.abc import Hashable
from dataclasses import dataclass
from datetime import datetime
from typing import cast, dataclass_transform, override
from uuid import UUID


@dataclass_transform(kw_only_default=True)
def entity[EntityClsT](cls: type[EntityClsT]) -> type[EntityClsT]:
    return dataclass(kw_only=True)(cls)


@entity
class Entity[EntityId: UUID](Hashable):
    id: EntityId
    created_at: datetime
    deleted_at: datetime | None = None

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entity):
            return cast("bool", type(self) is type(other) and self.id == other.id)

        return NotImplemented

    @override
    def __hash__(self) -> int:
        return hash(self.id)
