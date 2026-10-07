from collections import defaultdict
from typing import override

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dating_profile.data_gateway import DatingProfileDataGateway
from app.domain.dating_profile.entity import DatingProfile
from app.domain.dating_profile.value_objects import DatingProfileId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.mappers.dating_profile_mapper import DatingProfileMapper
from app.infra.persistence.sqla.rows import (
    DatingProfilePhotoRow,
    DatingProfileRow,
    DatingProfileTraitRow,
)
from app.infra.persistence.sqla.tables import (
    dating_profile_photo_table,
    dating_profile_table,
    dating_profile_trait_table,
)


class DefaultDatingProfileDataGateway(DatingProfileDataGateway):
    def __init__(
        self,
        session: AsyncSession,
        dating_profile_mapper: DatingProfileMapper,
    ) -> None:
        self._session = session
        self._mapper = dating_profile_mapper

    @override
    async def load_by_user_id(self, user_id: UserId) -> DatingProfile | None:
        result = await self._session.execute(
            select(DatingProfileRow).where(dating_profile_table.c.user_id == user_id),
        )
        profile_row = result.scalar_one_or_none()
        if profile_row is None:
            return None
        if profile_row.id is None:
            return None
        photos_result = await self._session.execute(
            select(DatingProfilePhotoRow).where(
                dating_profile_photo_table.c.dating_profile_id == profile_row.id,
            ),
        )
        photo_rows = list(photos_result.scalars().all())
        traits_result = await self._session.execute(
            select(DatingProfileTraitRow).where(
                dating_profile_trait_table.c.dating_profile_id == profile_row.id,
            ),
        )
        trait_rows = list(traits_result.scalars().all())
        return self._mapper.to_entity(profile_row, photo_rows, trait_rows)

    @override
    async def load_many_by_user_ids(self, user_ids: list[UserId]) -> dict[UserId, DatingProfile]:
        if not user_ids:
            return {}

        profiles_result = await self._session.execute(
            select(DatingProfileRow).where(dating_profile_table.c.user_id.in_(user_ids)),
        )
        profile_rows = [
            row for row in profiles_result.scalars().all() if row.id is not None and row.user_id is not None
        ]
        if not profile_rows:
            return {}

        dating_profile_ids = [row.id for row in profile_rows if row.id is not None]

        photos_result = await self._session.execute(
            select(DatingProfilePhotoRow).where(
                dating_profile_photo_table.c.dating_profile_id.in_(dating_profile_ids),
            ),
        )
        photo_rows = list(photos_result.scalars().all())
        photos_by_profile_id: dict[DatingProfileId, list[DatingProfilePhotoRow]] = defaultdict(list)
        for photo_row in photo_rows:
            if photo_row.dating_profile_id is None:
                continue
            photos_by_profile_id[DatingProfileId(photo_row.dating_profile_id)].append(photo_row)

        traits_result = await self._session.execute(
            select(DatingProfileTraitRow).where(
                dating_profile_trait_table.c.dating_profile_id.in_(dating_profile_ids),
            ),
        )
        trait_rows = list(traits_result.scalars().all())
        traits_by_profile_id: dict[DatingProfileId, list[DatingProfileTraitRow]] = defaultdict(list)
        for trait_row in trait_rows:
            if trait_row.dating_profile_id is None:
                continue
            traits_by_profile_id[DatingProfileId(trait_row.dating_profile_id)].append(trait_row)

        result: dict[UserId, DatingProfile] = {}
        for profile_row in profile_rows:
            if profile_row.id is None or profile_row.user_id is None:
                continue
            profile_id = DatingProfileId(profile_row.id)
            profile = self._mapper.to_entity(
                profile_row=profile_row,
                photo_rows=photos_by_profile_id.get(profile_id, []),
                trait_rows=traits_by_profile_id.get(profile_id, []),
            )
            result[UserId(profile_row.user_id)] = profile
        return result

    @override
    async def delete_photos_by_dating_profile_id(
        self,
        dating_profile_id: DatingProfileId,
    ) -> None:
        await self._session.execute(
            delete(dating_profile_photo_table).where(
                dating_profile_photo_table.c.dating_profile_id == dating_profile_id,
            ),
        )

    @override
    async def set_trait_hidden(
        self,
        dating_profile_id: DatingProfileId,
        trait_code: str,
        *,
        is_hidden: bool,
    ) -> None:
        await self._session.execute(
            update(dating_profile_trait_table)
            .where(
                dating_profile_trait_table.c.dating_profile_id == dating_profile_id,
                dating_profile_trait_table.c.trait_code == trait_code,
            )
            .values(is_hidden=is_hidden),
        )
