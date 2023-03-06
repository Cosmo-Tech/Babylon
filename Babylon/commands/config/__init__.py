from click import group

from .display import display
from .validate import validate
from .deployment import deployment
from .platform import platform
from .plugin import plugin

list_commands = [
    validate,
    display,
]

list_groups = [
    plugin,
    platform,
    deployment,
]


@group()
def config():
    """Group made to work on the config"""


for _command in list_commands:
    config.add_command(_command)

for _group in list_groups:
    config.add_command(_group)
