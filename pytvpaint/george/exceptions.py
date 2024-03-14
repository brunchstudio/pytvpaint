"""Custom George exceptions."""

from __future__ import annotations

from typing import Any


class GeorgeError(Exception):
    """George error exception.

    Used for return values in the `[ERROR]` section of functions in TVPaint's documentation.
    """

    def __init__(
        self, message: str | None = None, error_value: Any | None = None
    ) -> None:
        super().__init__(f"{message}" if message else "")
        self.error_value = error_value


class NoObjectWithIdError(GeorgeError):
    """Exception raised when a TVPaint was not found given its id."""

    def __init__(self, obj_id: int) -> None:
        super().__init__(f"Can't find an object with id: {obj_id}")
