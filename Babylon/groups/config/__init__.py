from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def config():
    """Group made to work on the config"""


for _command in list_commands:
    config.add_command(_command)

for _group in list_groups:
    config.add_command(_group)
