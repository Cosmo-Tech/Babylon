from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .get_currents import get_currents

list_commands = [
    get_currents,
    delete,
    get_all,
    get,
    create,
]


@group()
def connector():
    """Subgroup handling Connectors in the cosmotech API"""
    pass


for _command in list_commands:
    connector.add_command(_command)
