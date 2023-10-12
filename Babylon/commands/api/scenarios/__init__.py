from click import group
from .get_all import get_all

list_commands = [get_all]


@group()
def scenarios():
    """Scenarios - Cosmotech API"""
    pass


for _command in list_commands:
    scenarios.add_command(_command)
