from click import group

from .delete import delete
from .get import get
from .take_over import take_over
from .get_all import get_all
from .update_credentials import update_credentials
from .parameters import parameters

list_groups = [
    parameters
]


list_commands = [
    update_credentials,
    delete,
    get,
    take_over,
    get_all,
]


@group()
def dataset():
    """Command group handling PowerBI datasets"""
    pass


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)
