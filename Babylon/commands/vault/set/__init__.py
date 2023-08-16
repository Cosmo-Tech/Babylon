from click import group

from Babylon.utils.environment import Environment
from .set_global import set_global
from .babylon import set_babylon
from .project import project
from .platform import platform
from .user import set_user_secrets

env = Environment()

list_commands = [set_global, set_babylon, project, platform, set_user_secrets]


@group()
def set():
    """Group handling Vault Hashicorp"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    set.add_command(_command)
