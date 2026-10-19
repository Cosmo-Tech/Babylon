import pytest

from Babylon.commands.macro.helpers.common import resolve_inclusion_exclusion
from Babylon.core.errors import ConflictingSelectionError, InvalidOptionsError, UnknownResourceError
from Babylon.core.selection import ALLOWED_RESOURCES, resolve_resources

ORDER = ("build", "organization", "solution", "workspace", "webapp")  # order of the CLI tuple


def test_nothing_selects_everything():
    assert resolve_resources() == set(ALLOWED_RESOURCES)


def test_include_selects_only_those():
    assert resolve_resources(include=["solution", "workspace"]) == {"solution", "workspace"}


def test_exclude_removes_those():
    assert resolve_resources(exclude=["build", "webapp"]) == {"organization", "solution", "workspace"}


def test_include_and_exclude_conflict():
    with pytest.raises(ConflictingSelectionError):
        resolve_resources(include=["solution"], exclude=["build"])


def test_unknown_value_is_reported():
    with pytest.raises(UnknownResourceError) as exc:
        resolve_resources(include=["solution", "solutoin"])
    assert exc.value.invalid == ["solutoin"]


def test_errors_are_invalid_options():
    # One `except InvalidOptionsError` is enough for a caller (CLI or API).
    assert issubclass(ConflictingSelectionError, InvalidOptionsError)
    assert issubclass(UnknownResourceError, InvalidOptionsError)


@pytest.mark.parametrize(
    "include, exclude",
    [((), ()), (("solution",), ()), (("build", "webapp"), ()), ((), ("workspace",)), ((), ("build", "webapp"))],
)
def test_same_result_as_existing_cli_helper(include, exclude):
    """Safety net: the new function must give exactly the same answer as the current CLI code."""
    flags = resolve_inclusion_exclusion(include, exclude)
    expected = {name for name, selected in zip(ORDER, flags) if selected}
    assert resolve_resources(include, exclude) == expected
