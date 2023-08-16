import logging
import click

from .response import CommandResponse

logger = logging.getLogger("Babylon")


def run_command(command_line: list[str]) -> CommandResponse:
    """
    Helper used to run a command
    :param command_line: command line of the command to run
    :return: result of the command
    """
    context = click.get_current_context()
    if context.command_path == "babylon":
        root = context
    else:
        root = context.find_root()
    babylon = root.command
    ctx = babylon.make_context("babylon", [*command_line], ignore_unknown_options=True)
    ret: CommandResponse = babylon.invoke(ctx)
    logger.setLevel(logging.INFO)
    return ret
