from datetime import UTC, datetime

from app.domain.user.entity import User, UserId
from app.domain.user.value_objects import Profile
from app.infra.persistence.sqla.rows import ProfileRow, UserRow


class UserMapper:
    entity_type: type[User] = User

    @staticmethod
    def to_rows(user: User) -> list[UserRow | ProfileRow]:
        user_row = UserRow(
            id_=user.id,
            created_at=user.created_at,
            deleted_at=user.deleted_at,
        )
        if user.profile is None:
            return [user_row]
        now = datetime.now(tz=UTC)
        profile_row = ProfileRow(
            user_id=user.id,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            birth_date=user.profile.birth_date,
            gender=user.profile.gender,
            region=user.profile.region,
            avatar_url=user.profile.avatar_url,
            created_at=now,
            updated_at=now,
        )
        return [user_row, profile_row]

    @staticmethod
    def to_entity(user_row: UserRow, profile_row: ProfileRow | None) -> User:
        if user_row.id is None or user_row.created_at is None:
            msg = "UserRow must have id and created_at"
            raise ValueError(msg)
        profile: Profile | None = None
        if (
            profile_row is not None
            and profile_row.first_name
            and profile_row.birth_date is not None
            and profile_row.gender is not None
        ):
            profile = Profile(
                first_name=profile_row.first_name,
                last_name=profile_row.last_name,
                birth_date=profile_row.birth_date,
                gender=profile_row.gender,
                region=profile_row.region,
                avatar_url=profile_row.avatar_url,
            )
        return User(
            id=UserId(user_row.id),
            created_at=user_row.created_at,
            deleted_at=user_row.deleted_at,
            profile=profile,
        )
