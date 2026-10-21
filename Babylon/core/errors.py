"""Typed exceptions raised by Babylon.core.

The CLI turns them into click messages; an API can turn them into HTTP errors.
"""


class BabylonError(Exception):
    """Base class for every error raised by Babylon.core."""


class InvalidOptionsError(BabylonError, ValueError):
    """The caller supplied invalid options."""


class OperationInProgressError(BabylonError):
    """Another Babylon operation is already running in this process.

    Babylon stores the current context/tenant/variable files in the process-wide
    `Environment` singleton, so two operations in the same process would overwrite
    each other. Only one operation per process is allowed.
    """


class ConflictingSelectionError(InvalidOptionsError):
    """`include` and `exclude` were both provided."""


class UnknownResourceError(InvalidOptionsError):
    """`include`/`exclude` contains unknown resource kinds."""

    def __init__(self, invalid: list[str], allowed: tuple[str, ...]):
        self.invalid = invalid
        self.allowed = allowed
        super().__init__(f"Invalid resource type(s): {', '.join(invalid)}. Allowed values are: {', '.join(allowed)}")
