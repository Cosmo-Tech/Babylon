from click import group

from .get import get
from .get_all import get_all
from .update import update
from .delete import delete
from .create import create

list_commands = [
    get,
    get_all,
    update,
    delete,
    create,
]


@group()
def custom_domain():
    """Group interacting with Azure Static Webapps custom domains"""
    pass


for _command in list_commands:
    custom_domain.add_command(_command)
