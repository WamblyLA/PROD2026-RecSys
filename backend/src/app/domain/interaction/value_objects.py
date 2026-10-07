from enum import StrEnum
from typing import NewType
from uuid import UUID

InteractionId = NewType("InteractionId", UUID)


class InteractionType(StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"
    BLOCK = "block"
    UNBLOCK = "unblock"
