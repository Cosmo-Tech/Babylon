from click import group
from Babylon.utils.environment import Environment
from Babylon.commands.state.store import store
from Babylon.commands.state.copy import copy
from Babylon.commands.state.get import get

env = Environment()

list_commands = [store, copy, get]

list_groups = []


@group()
def state():
    """Group made to work on the babylon state"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    state.add_command(_command)

for _group in list_groups:
    state.add_command(_group)
