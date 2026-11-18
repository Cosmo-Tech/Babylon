from collections.abc import Iterator

import click
import pytest

from Babylon.commands.powerbi import powerbi
from Babylon.commands.powerbi.dataset.parameters.get import get
from Babylon.main import main


def _walk_commands(command: click.Command, parent: click.Context | None = None) -> Iterator[tuple[click.Command, click.Context]]:
    context = click.Context(command, info_name=command.name, parent=parent)
    yield command, context
    if isinstance(command, click.Group):
        for name in command.list_commands(context):
            child = command.get_command(context, name)
            assert child is not None
            yield from _walk_commands(child, context)


@pytest.mark.parametrize("root", [main, powerbi], ids=["babylon", "powerbi"])
@pytest.mark.filterwarnings("error:The parameter .* is used more than once:UserWarning")
def test_command_help_has_no_duplicate_options(root):
    for command, context in _walk_commands(root):
        with context:
            command.get_help(context)


@pytest.mark.parametrize(
    "options,workspace_id",
    [([], None), (["--workspace-id", "workspace-123"], "workspace-123")],
)
def test_get_dataset_parameters_parses_workspace_id(options, workspace_id):
    with get.make_context("get", [*options, "dataset-123"]) as context:
        assert context.params["workspace_id"] == workspace_id
        assert context.params["dataset_id"] == "dataset-123"
