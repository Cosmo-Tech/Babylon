from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all

list_commands = [
    get,
    delete,
    get_all,
    create,
]


@group()
def instance():
    """Subgroup dedicate to Azure digital twins instance management"""
    pass


for _command in list_commands:
    instance.add_command(_command)
