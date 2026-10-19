"""Typed exceptions raised by Babylon.core.

The CLI turns them into click messages; an API can turn them into HTTP errors.
"""


class BabylonError(Exception):
    """Base class for every error raised by Babylon.core."""


class InvalidOptionsError(BabylonError, ValueError):
    """The caller supplied invalid options."""


class ConflictingSelectionError(InvalidOptionsError):
    """`include` and `exclude` were both provided."""


class UnknownResourceError(InvalidOptionsError):
    """`include`/`exclude` contains unknown resource kinds."""

    def __init__(self, invalid: list[str], allowed: tuple[str, ...]):
        self.invalid = invalid
        self.allowed = allowed
        super().__init__(f"Invalid resource type(s): {', '.join(invalid)}. Allowed values are: {', '.join(allowed)}")
