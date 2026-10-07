from typing import override


class RecommendationProviderUnavailableError(Exception):
    @override
    def __str__(self) -> str:
        return "Recommendation provider unavailable"


class RecommendationCandidatesNotFoundError(Exception):
    def __init__(self, *, missing_count: int) -> None:
        self._missing_count = missing_count

    @property
    def missing_count(self) -> int:
        return self._missing_count

    @override
    def __str__(self) -> str:
        return f"Recommendation candidates not found in users: {self._missing_count}"
