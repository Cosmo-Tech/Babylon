import logging

from click import group
from Babylon.utils.environment import Environment
from Babylon.commands.azure.storage import storage
from Babylon.commands.azure.permission import permission
from Babylon.commands.azure.token import token

logger = logging.getLogger("Babylon")
env = Environment()

list_commands = []
list_groups = [storage, permission, token]


@group()
def azure():
    """Group allowing communication with Microsoft Azure Cloud"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _group in list_groups:
    azure.add_command(_group)

for _command in list_commands:
    azure.add_command(_command)
