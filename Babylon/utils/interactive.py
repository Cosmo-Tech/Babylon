from math import log10
from typing import Any
from typing import Optional

import click

MAX_RETRIES = 3


def element_to_str(element: Any, actual: Optional[Any] = None):
    """
    Add a box before the element to display
    Box will be ticked if element == actual
    :param element: The element to display
    :param actual: an element to compare the actual element
    :return: a string representation of the element prefixed with a box if actual is present
    """
    ret = []
    if actual is not None:
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
        selection = click.prompt("Enter your selection (use the id)", type=int)
        try:
            selected = elements[selection]
            return selected
        except:
            errors += 1
            if errors < MAX_RETRIES:
                click.echo(f"Invalid selection {MAX_RETRIES - errors} tries remaining")
            else:
                click.echo(f"Max number of tries reached.")
                return None
