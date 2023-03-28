from click import group

from .display import display
from .validate import validate
from .deployment import deployment
from .platform import platform
from .plugin import plugin
from .set_variable import set_variable
from .get_variable import get_variable
from .fill_template import fill_template
from .init import init

list_commands = [validate, display, get_variable, set_variable, fill_template, init]

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
