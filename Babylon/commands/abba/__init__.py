from click import group
from Babylon.commands.abba.run import run, check
from Babylon.utils.environment import Environment

env = Environment()


@group()
def abba():
    """Cosmotech ABBA"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


list_commands = [run, check]
list_groups = []

for _group in list_groups:
    abba.add_command(_group)

for _command in list_commands:
    abba.add_command(_command)