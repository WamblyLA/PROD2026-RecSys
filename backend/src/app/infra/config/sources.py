import os
from typing import overload


class EnvSource:
    @overload
    def get(self, key: str, default: str) -> str: ...

    @overload
    def get(self, key: str, default: None) -> str | None: ...

    @overload
    def get(self, key: str) -> str | None: ...

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the value of the environment variable with given key, or None if not present."""
        return os.getenv(key, default)

    def get_present_values(self, keys: list[str]) -> dict[str, str]:
        """Return a dict of values, filtering out keys that are not present in the environment."""
        unfiltered_values = {key: self.get(key) for key in keys}
        return {key: value for key, value in unfiltered_values.items() if value is not None}
