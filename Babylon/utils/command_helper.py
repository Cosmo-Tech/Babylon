import logging

import click

from .response import CommandResponse

logger = logging.getLogger("Babylon")


def run_command(command_line: list[str], log_level=logging.WARNING, raise_error: bool = True) -> CommandResponse:
    """
    Helper used to run a command
    :param command_line: command line of the command to run
    :return: result of the command
    """
    logger.debug(f"Running command: {' '.join(command_line)}")
    old_log_level = logger.level
    if old_log_level < log_level:
        logger.setLevel(log_level)
    root = click.get_current_context().find_root()
    babylon = root.command
    ctx = click.Context(babylon, parent=root)
    name, cmd, args = babylon.resolve_command(ctx, command_line)
    cmd.parse_args(ctx, args)
    ret = cmd.invoke(ctx)
    if raise_error:
        ret.assert_error()
    logger.setLevel(old_log_level)
    return ret
