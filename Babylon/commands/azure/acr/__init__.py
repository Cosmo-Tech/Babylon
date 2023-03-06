from click import group

from ....utils.decorators import requires_external_program
from .delete import delete
from .list import list
from .pull import pull
from .push import push

list_commands = [
    delete,
    list,
    push,
    pull,
]


@group()
@requires_external_program("docker")
def acr():
    """Group interacting with Azure Container Registry"""


for _command in list_commands:
    acr.add_command(_command)
