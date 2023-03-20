from click import group

from .display import display
from .validate import validate
from .deployment import deployment
from .platform import platform
from .plugin import plugin
from .set_variable import set_variable
from .fill_template import fill_template
from .initialize import initialize

list_commands = [validate, display, set_variable, fill_template, initialize]

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
