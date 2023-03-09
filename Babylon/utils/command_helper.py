import logging

import click

from .response import CommandResponse

logger = logging.getLogger("Babylon")


def run_command(command_line: list[str], log_level: int = logging.WARNING) -> CommandResponse:
    """
    Helper used to run a command
    :param command_line: command line of the command to run
    :return: result of the command
    """
    logger.debug(f"Running command: {' '.join(command_line)}")
    old_log_level = logger.level
    if old_log_level < log_level:
        logger.setLevel(log_level)
    context = click.get_current_context()
    if context.command_path == "babylon":
        root = context
    else:
        root = context.find_root()
    babylon = root.command
    ctx = babylon.make_context("babylon", command_line, ignore_unknown_options=True)
    ret: CommandResponse = babylon.invoke(ctx)
    logger.setLevel(old_log_level)
    return ret
