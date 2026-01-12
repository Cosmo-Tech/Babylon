import logging

from click import group

from Babylon.commands.azure.permission import permission
from Babylon.commands.azure.storage import storage
from Babylon.commands.azure.token import token
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()

list_commands = []
list_groups = [storage, permission, token]


@group()
def azure():
    """Group allowing communication with Microsoft Azure Cloud"""
    pass

for _group in list_groups:
    azure.add_command(_group)

for _command in list_commands:
    azure.add_command(_command)
