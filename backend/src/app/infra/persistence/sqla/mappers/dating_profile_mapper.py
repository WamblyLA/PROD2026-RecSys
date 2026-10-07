from uuid_utils.compat import uuid7

from app.domain.dating_profile.entity import DatingProfile
from app.domain.dating_profile.value_objects import (
    DatingProfileId,
    UserTrait,
)
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import (
    DatingProfilePhotoRow,
    DatingProfileRow,
    DatingProfileTraitRow,
)


class DatingProfileMapper:
    entity_type: type[DatingProfile] = DatingProfile

    @staticmethod
    def to_rows(
        profile: DatingProfile,
    ) -> list[DatingProfileRow | DatingProfilePhotoRow]:
        rows: list[DatingProfileRow | DatingProfilePhotoRow] = [
            DatingProfileRow(
                id_=profile.id,
                user_id=profile.user_id,
                created_at=profile.created_at,
                deleted_at=profile.deleted_at,
            ),
        ]
        rows.extend(
            DatingProfilePhotoRow(
                id_=uuid7(),
                dating_profile_id=profile.id,
                url=url,
                position=i,
            )
            for i, url in enumerate(profile.photos)
        )
        return rows

    @staticmethod
    def to_entity(
        profile_row: DatingProfileRow,
        photo_rows: list[DatingProfilePhotoRow],
        trait_rows: list[DatingProfileTraitRow],
    ) -> DatingProfile:
        if profile_row.id is None or profile_row.user_id is None or profile_row.created_at is None:
            msg = "DatingProfileRow must have id, user_id, created_at"
            raise ValueError(msg)
        photos = [pr.url for pr in sorted(photo_rows, key=lambda r: r.position or 0) if pr.url is not None]
        traits = [
            UserTrait(
                trait_code=tr.trait_code or "",
                score=tr.score or 0.0,
                is_hidden=tr.is_hidden or False,
            )
            for tr in trait_rows
            if tr.trait_code is not None and tr.score is not None and tr.is_hidden is not None
        ]
        return DatingProfile(
            id=DatingProfileId(profile_row.id),
            created_at=profile_row.created_at,
            deleted_at=profile_row.deleted_at,
            user_id=UserId(profile_row.user_id),
            photos=photos,
            traits=traits,
        )
