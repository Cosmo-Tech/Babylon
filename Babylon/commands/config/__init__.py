from click import group
from Babylon.utils.environment import Environment
from Babylon.commands.config.set import set
from Babylon.commands.config.get import get
from Babylon.commands.config.init import init
from Babylon.commands.config.upload import upload
from Babylon.commands.config.display import display

env = Environment()

list_commands = [
    set,
    get,
    init,
    upload,
    display,
]

list_groups = []


@group()
def config():
    """Group made to work on the config"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _command in list_commands:
    config.add_command(_command)

for _group in list_groups:
    config.add_command(_group)
