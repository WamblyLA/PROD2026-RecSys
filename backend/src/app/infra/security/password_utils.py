import hmac
from typing import override

from cryptography.fernet import Fernet, InvalidToken

from app.application.user.password_utils import PasswordHasher, PasswordVerifier


class FernetPasswordService(PasswordHasher, PasswordVerifier):
    def __init__(self, fernet: Fernet) -> None:
        self._fernet = fernet

    @override
    def hash(self, password: str) -> str:
        raw: bytes = self._fernet.encrypt(password.encode("utf-8"))
        return raw.decode("utf-8")

    @override
    def verify(
        self,
        verifiable_password: str,
        hashed_password: str,
    ) -> bool:
        try:
            decrypted_password = self._fernet.decrypt(hashed_password.encode("utf-8")).decode("utf-8")
            return hmac.compare_digest(verifiable_password, decrypted_password)
        except (InvalidToken, ValueError, TypeError, UnicodeDecodeError):
            return False
