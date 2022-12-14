import click
from typing import Any


def run_command(command_line: list[str]) -> Any:
    """
    Helper used to run a command
    :param command_line: command line of the command to run
    :return: result of the command
    """
    root = click.get_current_context().find_root()
    cmd = root.command

    ctx = click.Context(cmd, parent=root)
    cmd.parse_args(ctx, command_line)
    ret = cmd.invoke(ctx)
    return ret
