from click import group
from .create import create

list_commands = [create]


@group()
def payload():
    """Create a payload from API resource"""


for _group in list_commands:
    payload.add_command(_group)
