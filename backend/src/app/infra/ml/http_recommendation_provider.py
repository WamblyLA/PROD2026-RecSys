from collections.abc import Mapping
from typing import Any, override

import httpx
import structlog

from app.application.recommendation.dto import RecommendationItem
from app.application.recommendation.errors import RecommendationProviderUnavailableError
from app.application.recommendation.protocol import RecommendationProvider
from app.domain.user.entity import UserId

logger = structlog.get_logger(__name__)


class HttpRecommendationProvider(RecommendationProvider):
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    @override
    async def get_recommendations(self, *, user_id: UserId) -> list[RecommendationItem]:
        if not self._base_url:
            raise RecommendationProviderUnavailableError
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url=f"{self._base_url}/recommendation",
                    json={"user_id": str(user_id)},
                )
        except httpx.HTTPError as error:
            raise RecommendationProviderUnavailableError from error

        if response.status_code >= 400:
            raise RecommendationProviderUnavailableError

        payload = self._parse_payload(response)
        items: list[RecommendationItem] = []
        for raw_item in payload:
            item = self._build_item(raw_item=raw_item, user_id=user_id)
            if item is not None:
                items.append(item)
        return items

    def _parse_payload(self, response: httpx.Response) -> list[dict[str, Any]]:
        try:
            raw_payload = response.json()
        except ValueError as error:
            logger.warning("ml_recommendation_invalid_payload", reason="response_not_json", exc_info=error)
            raise RecommendationProviderUnavailableError from error

        if isinstance(raw_payload, dict) and "items" in raw_payload:
            raw_payload = raw_payload["items"]
        if not isinstance(raw_payload, list):
            logger.warning(
                "ml_recommendation_invalid_payload", reason="payload_not_list", type_=type(raw_payload).__name__
            )
            raise RecommendationProviderUnavailableError
        return [item for item in raw_payload if isinstance(item, dict)]

    def _build_item(self, *, raw_item: dict[str, Any], user_id: UserId) -> RecommendationItem | None:
        ml_recommendation_id = raw_item.get("ml_recommendation_id")
        candidate_user_id = raw_item.get("candidate_user_id")
        if not isinstance(ml_recommendation_id, str) or not isinstance(candidate_user_id, str):
            return None

        reasons = self._parse_reasons(raw_item.get("reasons"))
        return RecommendationItem(
            ml_recommendation_id=ml_recommendation_id,
            user_id=str(user_id),
            candidate_user_id=candidate_user_id,
            reasons=reasons,
        )

    def _parse_reasons(self, raw_reasons: object) -> dict[str, float]:
        if not isinstance(raw_reasons, Mapping):
            logger.warning(
                "ml_recommendation_invalid_reasons",
                reason="reasons_not_mapping",
                type_=type(raw_reasons).__name__,
            )
            raise RecommendationProviderUnavailableError

        result: dict[str, float] = {}
        for raw_name, raw_score in raw_reasons.items():
            if not isinstance(raw_name, str):
                logger.warning(
                    "ml_recommendation_invalid_reasons",
                    reason="reason_key_not_str",
                    key_type=type(raw_name).__name__,
                    key_repr=repr(raw_name),
                )
                raise RecommendationProviderUnavailableError
            try:
                result[raw_name] = float(raw_score)
            except (TypeError, ValueError) as err:
                logger.warning(
                    "ml_recommendation_invalid_reasons",
                    reason="reason_value_not_float",
                    key=raw_name,
                    value_repr=repr(raw_score),
                    exc_info=err,
                )
                raise RecommendationProviderUnavailableError from err
        return result
