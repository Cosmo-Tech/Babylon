from click import group

from .delete import delete
from .get import get
from .get_all import get_all
from .set import set

list_commands = [
    delete,
    set,
    get_all,
    get,
]


@group()
def permission():
    """Group interacting with ADX permissions"""
    pass


for _command in list_commands:
    permission.add_command(_command)
