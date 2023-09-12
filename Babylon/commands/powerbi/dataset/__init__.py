from click import group
from .delete import delete
from .get import get
from .take_over import take_over
from .get_all import get_all
from .parameters import parameters
from .users import users
from .update_credentials import update_credentials

list_groups = [parameters]

list_commands = [
    delete,
    get,
    take_over,
    get_all,
    users,
    update_credentials,
]


@group()
def dataset():
    """Command group handling PowerBI datasets"""
    pass


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)
