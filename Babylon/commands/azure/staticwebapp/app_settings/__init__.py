from click import group

from .get import get
from .update import update

list_commands = [
    get,
    update,
]


@group()
def app_settings():
    """Group initialized from a template"""
    pass


for _command in list_commands:
    app_settings.add_command(_command)
