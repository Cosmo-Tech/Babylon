from click import group

from .update import update
from .delete import delete
from .create import create
from .get import get
from .get_all import get_all
from .app_settings import app_settings
from .custom_domain import custom_domain

list_commands = [
    update,
    delete,
    create,
    get,
    get_all,
]

list_groups = [
    app_settings,
    custom_domain,
]


@group()
def staticwebapp():
    """Group interacting with Azure Static Webapps"""


for _command in list_commands:
    staticwebapp.add_command(_command)

for _group in list_groups:
    staticwebapp.add_command(_group)
