from click import group
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .last_run import last_run
from .outputs import outputs
from .run import run
from .vars import vars

list_commands = [
    create,
    delete,
    get,
    get_all,
    last_run,
    outputs,
    run,
]

list_groups = [
    vars,
]


@group()
def workspace():
    """Sub-group allowing interaction with the organization of the Terraform Cloud API"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)
