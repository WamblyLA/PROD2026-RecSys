from typing import override
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken

from app.application.access_token.cryptographer import AccessTokenCryptographer, RawAccessToken
from app.domain.access_token.entity import AccessTokenId


class FernetAccessTokenCryptographer(AccessTokenCryptographer):
    def __init__(self, fernet: Fernet) -> None:
        self._fernet = fernet

    @override
    def crypto(self, access_token_id: AccessTokenId) -> RawAccessToken:
        raw: bytes = self._fernet.encrypt(str(access_token_id).encode("utf-8"))
        return raw.decode("utf-8")

    @override
    def decrypto(self, raw_access_token: RawAccessToken) -> AccessTokenId | None:
        try:
            return AccessTokenId(
                UUID(
                    self._fernet.decrypt(raw_access_token.encode("utf-8")).decode("utf-8"),
                ),
            )
        except InvalidToken:
            return None
