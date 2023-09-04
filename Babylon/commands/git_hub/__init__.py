from click import group
from Babylon.utils.environment import Environment
from .runs import runs

list_commands = [runs]

env = Environment()


@group()
def github():
    """Group allowing communication with Github REST API"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    github.add_command(_command)
