import logging
import sys
import click

from math import log10
from typing import Any
from typing import Optional
from ..version import VERSION

MAX_RETRIES = 3
INTERACTIVE_ARG_VALUE = "--interactive-after"

logger = logging.getLogger("Babylon")


def ask_for_group(prompt: str, exists: bool = False) -> list[str]:
    """
    Will prompt the user to get a group
    :param prompt: Which text should be prompted to the user ?
    :param exists: Should the group exists ?
    :return: the list of subgroups composing the path to the group
    """

    group_string = click.prompt(prompt, type=str)
    if exists:
        # TODO : Check for group existence
        pass
    click.echo(f"Selected group : {group_string}")
    return group_string.split()


def element_to_str(element: Any, actual: Optional[Any] = None):
    """
    Add a box before the element to display
    Box will be ticked if element == actual
    :param element: The element to display
    :param actual: an element to compare the actual element
    :return: a string representation of the element prefixed with a box if actual is present
    """
    ret = []
    if actual:
        ret.append("[x]" if actual == element else "[ ]")
    ret.append(str(element))
    return " - ".join(ret)


def select_from_list(elements: list[Any], actual: Optional[Any] = None) -> Optional[Any]:
    """
    Start a prompt with 3 retries to select an element in a list
    :param elements: list of elements to chose
    :param actual: an element that can be part of the list which is the current choice
    :return: The element selected by the user
    """
    errors = 0
    if not elements:
        return None
    while True:
        if errors == 0:
            click.echo("Select an element in the following list:")
            index = 0
            list_len = int(log10(len(elements))) + 1
            for element in elements:
                click.echo(f"{index:>{list_len}} - {element_to_str(element, actual)}")
                index += 1
        selection = click.prompt("Enter your selection (use the id)", type=int)
        try:
            selected = elements[selection]
            return selected
        except IndexError:
            errors += 1
            if errors < MAX_RETRIES:
                click.echo(f"Invalid selection {MAX_RETRIES - errors} tries remaining")
            else:
                click.echo("Max number of tries reached.")
                return None


def confirm_deletion(entity_type: str, entity_id: str) -> bool:
    """Ask for confirmation for deletion of an object
    :param entity_type: Entity type
    :param entity_id: Entity ID
    :return: Should execution continue ?
    """
    if not click.confirm(f"You are trying to delete {entity_type} {entity_id} \nDo you want to continue ?"):
        logger.info(f"{entity_type} deletion aborted.")
        return False
    for _ in range(0, MAX_RETRIES):
        confirm_connector_id = click.prompt(f"Confirm deletion by typing {entity_type} ID: '{entity_id}'")
        if confirm_connector_id != entity_id:
            logger.error(f"Wrong {entity_type}, "
                         f"to confirm deletion, please type {entity_type} ID: '{entity_id}'")
            continue
        return True
    logger.error(f"{entity_type} deletion aborted")
    return False


def confirm_deploy_arm_mode() -> bool:
    """Ask for confirmation for continue on incremental mode or not
    :return: Should execution continue ?
    """
    if not click.confirm("You are trying to deploy arm in complete mode. \nDo you want to continue ?"):
        return False
    return True


def interactive_run(command_return, interactive: bool = False, **kwargs):
    if not interactive:
        return command_return
    from .command_helper import run_command
    import code
    _locals = dict(globals(), **{"command_return": command_return, "run_command": run_command})
    shell = code.InteractiveConsole(locals=_locals)
    sys.ps1 = "Babylon > "
    import readline
    from rlcompleter import Completer
    completer = Completer(namespace=_locals)
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab:complete')
    shell.interact(banner="Babylon interactive mode.\n"
                   f"Babylon version: {VERSION}\n"
                   "Result of command is in var `command_return`\n"
                   "You can run another command using function `run_command`",
                   exitmsg="Thanks for using Babylon")
