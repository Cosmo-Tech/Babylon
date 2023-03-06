from click import group

from .create import create
from .delete import delete
from .get import get
from .list import list

list_commands = [
    get,
    delete,
    list,
    create,
]


@group()
def instance():
    """Subgroup dedicate to Azure digital twins instance management"""
    pass


for _command in list_commands:
    instance.add_command(_command)
