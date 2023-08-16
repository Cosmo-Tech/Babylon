from click import group

from Babylon.utils.environment import Environment
from .get_global import get_global
from .babylon import get_babylon
from .project import project
from .platform import platform
from .user import get_user_secrets

env = Environment()

list_commands = [get_global, get_babylon, project, platform, get_user_secrets]


@group()
def get():
    """Group handling Vault Hashicorp"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    get.add_command(_command)
