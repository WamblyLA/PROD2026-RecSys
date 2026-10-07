from app.domain.auth_identity.entity import AuthIdentity
from app.domain.auth_identity.value_objects import AuthIdentityId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import AuthIdentityRow


class AuthIdentityMapper:
    entity_type: type[AuthIdentity] = AuthIdentity

    @staticmethod
    def to_rows(identity: AuthIdentity) -> list[AuthIdentityRow]:
        return [
            AuthIdentityRow(
                id_=identity.id,
                user_id=identity.user_id,
                method=identity.method,
                identifier=identity.identifier,
                secret_key=identity.secret_key,
                deleted_at=identity.deleted_at,
                created_at=identity.created_at,
            ),
        ]

    @staticmethod
    def to_entity(row: AuthIdentityRow) -> AuthIdentity:
        if (
            row.id is None
            or row.user_id is None
            or row.method is None
            or row.identifier is None
            or row.created_at is None
        ):
            msg = "AuthIdentityRow must have id, user_id, method, identifier, created_at"
            raise ValueError(msg)
        return AuthIdentity(
            id=AuthIdentityId(row.id),
            user_id=UserId(row.user_id),
            method=row.method,
            identifier=row.identifier,
            secret_key=row.secret_key,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
        )
