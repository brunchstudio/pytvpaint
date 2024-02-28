from __future__ import annotations

from typing import Any


class GeorgeError(Exception):
    def __init__(
        self, message: str | None = None, error_value: Any | None = None
    ) -> None:
        super().__init__(f"{message}" if message else "")
        self.error_value = error_value


class NoObjectWithIdError(GeorgeError):
    def __init__(self, obj_id: int) -> None:
        super().__init__(f"Can't find an object with id: {obj_id}")
