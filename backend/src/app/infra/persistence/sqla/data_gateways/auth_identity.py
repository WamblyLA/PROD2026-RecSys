from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth_identity.data_gateway import AuthIdentityDataGateway
from app.domain.auth_identity.entity import AuthIdentity
from app.domain.auth_identity.value_objects import AuthMethod
from app.infra.persistence.sqla.mappers.auth_identity_mapper import AuthIdentityMapper
from app.infra.persistence.sqla.rows import AuthIdentityRow
from app.infra.persistence.sqla.tables import auth_identity_table


class DefaultAuthIdentityDataGateway(AuthIdentityDataGateway):
    def __init__(self, session: AsyncSession, auth_identity_mapper: AuthIdentityMapper) -> None:
        self._session = session
        self._auth_identity_mapper = auth_identity_mapper

    @override
    async def load_by_method_and_identifier(
        self,
        method: AuthMethod,
        identifier: str,
    ) -> AuthIdentity | None:
        statement = select(AuthIdentityRow).where(
            auth_identity_table.c.method == method,
            auth_identity_table.c.identifier == identifier,
            auth_identity_table.c.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        row = result.scalar_one_or_none()
        return self._auth_identity_mapper.to_entity(row) if row is not None else None
