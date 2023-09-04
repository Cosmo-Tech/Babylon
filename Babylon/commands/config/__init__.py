from click import group
from Babylon.utils.environment import Environment
from .set import set
from .get import get
from .init import init
from .upload import upload
from .display import display

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
