from app.domain.access_token.entity import AccessToken, AccessTokenId
from app.domain.user.entity import UserId
from app.infra.persistence.sqla.rows import AccessTokenRow


class AccessTokenMapper:
    entity_type: type[AccessToken] = AccessToken

    @staticmethod
    def to_rows(token: AccessToken) -> list[AccessTokenRow]:
        return [
            AccessTokenRow(
                id_=token.id,
                user_id=token.user_id,
                revoked=token.revoked,
                expires_in=token.expires_in,
                deleted_at=token.deleted_at,
                created_at=token.created_at,
            ),
        ]

    @staticmethod
    def to_entity(row: AccessTokenRow) -> AccessToken:
        if (
            row.id is None
            or row.user_id is None
            or row.revoked is None
            or row.expires_in is None
            or row.created_at is None
        ):
            msg = "AccessTokenRow must have id, user_id, revoked, expires_in, created_at"
            raise ValueError(msg)
        return AccessToken(
            id=AccessTokenId(row.id),
            user_id=UserId(row.user_id),
            revoked=row.revoked,
            expires_in=row.expires_in,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
        )
