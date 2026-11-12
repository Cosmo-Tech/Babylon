import pytest
from click import Abort

from Babylon.commands.macro.helpers.common import resolve_inclusion_exclusion, validate_inclusion_exclusion
from Babylon.core.errors import ConflictingSelectionError, InvalidOptionsError, UnknownResourceError
from Babylon.core.selection import ALLOWED_RESOURCES, resolve_resources


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


# Test CLI helper functions
@pytest.mark.parametrize(
    "include, exclude, expected",
    [
        ((), (), (True, True, True, True, True)),
        (("solution",), (), (False, False, True, False, False)),
        (("build", "webapp"), (), (True, False, False, False, True)),
        ((), ("workspace",), (True, True, True, False, True)),
        ((), ("build", "webapp"), (False, True, True, True, False)),
    ],
)
def test_cli_helper_keeps_historical_tuple(include, exclude, expected):
    """The CLI helper now delegates to the core, but must keep returning the same 5-boolean tuple
    in the order (build, organization, solution, workspace, webapp) used by apply.py / destroy.py."""
    assert resolve_inclusion_exclusion(include, exclude) == expected


def test_cli_helper_shows_conflict_message_and_aborts(capsys, caplog):
    with pytest.raises(Abort):
        validate_inclusion_exclusion(("solution",), ("build",))
    assert "Argument Conflict" in capsys.readouterr().out
    assert "Cannot use [bold]--include[/bold] and [bold]--exclude[/bold] at the same time" in caplog.text


def test_cli_helper_lists_every_invalid_value_and_aborts(capsys, caplog):
    with pytest.raises(Abort):
        validate_inclusion_exclusion(("solutoin", "foo"), ())
    assert "Invalid Arguments Detected" in capsys.readouterr().out
    assert "solutoin[/yellow] is not a valid resource type" in caplog.text
    assert "foo[/yellow] is not a valid resource type" in caplog.text
    assert "Allowed values are: [cyan]build, organization, solution, workspace, webapp[/cyan]" in caplog.text
