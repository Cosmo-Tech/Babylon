from click import group

from .delete import delete
from .get import get
from .get_all import get_all
from .create import create

list_commands = [delete, get, get_all, create]


@group()
def appinsight():
    """Group interacting with Azure App Insight"""


for _command in list_commands:
    appinsight.add_command(_command)
