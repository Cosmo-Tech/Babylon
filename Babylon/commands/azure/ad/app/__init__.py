from click import group
from .password import password
from .create import create
from .delete import delete
from .get_all import get_all
from .get_principal import get_principal
from .get import get
from .update import update

list_commands = [create, delete, get_all, get_principal, get, update]

list_groups = [password]


@group()
def app():
    """Azure Active Directory Apps"""
    pass


for _command in list_commands:
    app.add_command(_command)

for _group in list_groups:
    app.add_command(_group)
