from enum import StrEnum
from typing import NewType
from uuid import UUID

AuthIdentityId = NewType("AuthIdentityId", UUID)


class AuthMethod(StrEnum):
    EMAIL = "email"
    YANDEX = "yandex"
