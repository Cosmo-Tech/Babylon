"""Resolution of the `--include` / `--exclude` options, without any click dependency."""

from collections.abc import Iterable

from Babylon.core.errors import ConflictingSelectionError, UnknownResourceError

# Same values and order as the historical CLI validation (helpers/common.py).
ALLOWED_RESOURCES: tuple[str, ...] = ("build", "organization", "solution", "workspace", "webapp")


def resolve_resources(include: Iterable[str] = (), exclude: Iterable[str] = ()) -> frozenset[str]:
    """Return the set of resource kinds selected by `include` / `exclude`.

    - nothing given  -> every resource
    - include given  -> only those resources
    - exclude given  -> every resource except those

    Raises:
        ConflictingSelectionError: both `include` and `exclude` are given.
        UnknownResourceError: a value is not a known resource kind.
    """
    include = tuple(include)
    exclude = tuple(exclude)

    if include and exclude:
        raise ConflictingSelectionError("Cannot use include and exclude at the same time")

    invalid = [value for value in include + exclude if value not in ALLOWED_RESOURCES]
    if invalid:
        raise UnknownResourceError(invalid, ALLOWED_RESOURCES)

    if include:
        return frozenset(include)
    return frozenset(r for r in ALLOWED_RESOURCES if r not in exclude)
