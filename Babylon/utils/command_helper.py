import click
from typing import Any


def run_command(command_line: list[str]) -> Any:
    """
    Helper used to run a command
    :param command_line: command line of the command to run
    :return: result of the command
    """
    root = click.get_current_context().find_root()
    babylon = root.command
    ctx = click.Context(babylon, parent=root)
    name, cmd, args = babylon.resolve_command(ctx, command_line)
    cmd.parse_args(ctx, args)
    ret = cmd.invoke(ctx)
    return ret
