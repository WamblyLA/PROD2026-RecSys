from dataclasses import dataclass
from typing import override


@dataclass(frozen=True, slots=True)
class NotificationDeviceNotFoundError(Exception):
    @override
    def __str__(self) -> str:
        return "Notification device not found"
