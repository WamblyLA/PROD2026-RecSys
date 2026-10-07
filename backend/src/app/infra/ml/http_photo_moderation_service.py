from base64 import b64encode
from typing import Any, override

import httpx

from app.application.dating_profile.errors import (
    PhotoModerationRejectedError,
    PhotoModerationUnavailableError,
)
from app.application.dating_profile.photo_moderation import PhotoModerationService


class HttpPhotoModerationService(PhotoModerationService):
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    @override
    async def ensure_photo_allowed(
        self,
        *,
        content: bytes,
        content_type: str,
    ) -> None:
        if not self._base_url:
            raise PhotoModerationUnavailableError
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url=f"{self._base_url}/photos/moderation",
                    json={
                        "content_base64": b64encode(content).decode("ascii"),
                        "content_type": content_type,
                    },
                )
        except httpx.HTTPError as error:
            raise PhotoModerationUnavailableError from error

        if response.status_code >= 500:
            raise PhotoModerationUnavailableError
        if response.status_code >= 400:
            raise PhotoModerationRejectedError

        payload = self._parse_payload(response)
        if not payload.get("allowed", False):
            raise PhotoModerationRejectedError

    def _parse_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            raise PhotoModerationUnavailableError from error
        if not isinstance(payload, dict):
            raise PhotoModerationUnavailableError
        if "allowed" not in payload and "is_allowed" in payload:
            payload["allowed"] = bool(payload["is_allowed"])
        return payload
