from click import group

from .login import login
from .set import set
from .get import get

list_commands = [
    login,
    set,
    get,
]


@group(name="hvac")
def vault():
    """Group handling Vault Hashicorp"""
    pass


for _command in list_commands:
    vault.add_command(_command)
