from json import JSONDecodeError
from typing import Any, override

import httpx

from app.application.oauth.protocol import (
    OAuthClient,
    OAuthExchangeCodeError,
    OAuthLoadUserInfoError,
    OAuthTokenResponse,
    OAuthUserInfo,
)
from app.presentation.api.config.models import YandexOAuthConfig


class YandexOAuthClient(OAuthClient):
    def __init__(
        self,
        config: YandexOAuthConfig,
        *,
        timeout: float = 10.0,
    ) -> None:
        self._client_id = config.client_id
        self._client_secret = config.client_secret
        self._timeout = timeout

        self._token_url = "https://oauth.yandex.ru/token"  # noqa: S105
        self._userinfo_url = "https://login.yandex.ru/info"
        self._avatar_url_interpolate = "https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"

    @override
    async def exchange_code(self, code: str) -> OAuthTokenResponse:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                )
                response.raise_for_status()
                data = response.json()

        except (httpx.HTTPError, JSONDecodeError) as e:
            raise OAuthExchangeCodeError from e

        return OAuthTokenResponse(
            access_token=data["access_token"],
            expires_in=data.get("expires_in"),
        )

    @override
    async def load_user_info(self, access_token: str) -> OAuthUserInfo:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    self._userinfo_url,
                    params={"format": "json"},
                    headers={"Authorization": f"OAuth {access_token}"},
                )
                response.raise_for_status()
                data = response.json()

        except (httpx.HTTPError, JSONDecodeError) as e:
            raise OAuthLoadUserInfoError from e

        return OAuthUserInfo(
            user_id=str(data["id"]),
            email=data.get("default_email"),
            display_name=data.get("display_name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            avatar_url=self._extract_avatar(data),
            phone=(data.get("default_phone") or {}).get("number"),
        )

    def _extract_avatar(self, data: dict[str, Any]) -> str | None:
        avatar_id = data.get("default_avatar_id")

        if not avatar_id or not isinstance(avatar_id, str):
            return None

        return self._avatar_url_interpolate.format(avatar_id=avatar_id)
